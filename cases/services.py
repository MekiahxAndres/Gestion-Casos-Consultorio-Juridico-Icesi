"""
Services para la funcionalidad de Reparto de Casos (HU3).

Este módulo contiene la lógica de negocio para la asignación manual y automática
de casos, validación de completitud y gestión de etapas.
"""

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from accounts.models import User
from .models import BitacoraEntry, Case, CaseAppointment, CaseAssignment, CaseDeadline, CaseDocument

logger = logging.getLogger(__name__)


ACTIVE_ASSIGNED_CASE_STATUSES = [
    Case.CaseStatus.ASIGNADO,
    Case.CaseStatus.AUTOASIGNADO,
    Case.CaseStatus.EN_PROCESO,
    Case.CaseStatus.ESPERANDO_BENEFICIARIO,
    Case.CaseStatus.EN_REVISION,
]

REQUIRED_CASE_DOCUMENT_TYPES = [
    CaseDocument.DocumentType.DOCUMENTO,
    CaseDocument.DocumentType.RECIBO_SERVICIOS,
    CaseDocument.DocumentType.FOTO,
]

UNCATEGORIZED_CATEGORY_KEY = "__uncategorized__"
UNCATEGORIZED_CATEGORY_LABEL = "Sin sala"
UNTYPED_CASE_TYPE_KEY = "__untyped__"
UNTYPED_CASE_TYPE_LABEL = "Sin trámite"


def get_active_assigned_cases_queryset():
    valid_type_filters = Q()
    for category_code, type_choices in get_category_type_choices().items():
        valid_type_filters |= Q(
            category=category_code,
            case_type_specific__in=type_choices.keys(),
        )

    return Case.objects.filter(
        assigned_student__isnull=False,
        status__in=ACTIVE_ASSIGNED_CASE_STATUSES,
    ).filter(valid_type_filters).annotate(
        valid_required_document_count=Count(
            "case_documents__document_type",
            filter=Q(
                case_documents__document_type__in=REQUIRED_CASE_DOCUMENT_TYPES,
                case_documents__is_valid=True,
            ),
            distinct=True,
        )
    ).filter(valid_required_document_count=len(REQUIRED_CASE_DOCUMENT_TYPES))


def get_category_type_choices():
    return {
        Case.CaseCategory.PENAL: dict(Case.PenalType.choices),
        Case.CaseCategory.LABORAL: dict(Case.LaboralType.choices),
        Case.CaseCategory.CIVIL: dict(Case.CivilType.choices),
        Case.CaseCategory.FAMILIA: dict(Case.FamiliaType.choices),
        Case.CaseCategory.PUBLICO: dict(Case.PublicoType.choices),
        Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES: dict(Case.DerechoPublicoMigrantesType.choices),
        Case.CaseCategory.PUBLICO_MIGRANTES: dict(Case.PublicoMigrantesType.choices),
    }


def get_case_assignment_missing_fields(case):
    missing_fields = []
    type_choices = get_category_type_choices()

    if not case.assigned_student_id:
        missing_fields.append("estudiante")

    if not case.category:
        missing_fields.append("sala")

    if not case.case_type_specific:
        missing_fields.append("trámite")
    elif case.category and case.case_type_specific not in type_choices.get(case.category, {}):
        missing_fields.append("trámite válido para la sala")

    if case.status not in ACTIVE_ASSIGNED_CASE_STATUSES:
        missing_fields.append("estado activo")

    completion = CaseCompletionValidator.is_complete(case)
    if not completion["is_complete"]:
        missing_fields.append("documentos requeridos válidos")

    return missing_fields


def is_case_assignment_complete(case):
    return not get_case_assignment_missing_fields(case)


def get_case_assignment_state(case):
    if is_case_assignment_complete(case):
        return "assigned"

    if (
        case.status == Case.CaseStatus.SIN_ASIGNAR
        and not case.assigned_student_id
    ):
        return "unassigned"

    return "incomplete"


def build_assigned_cases_category_summary(cases):
    type_choices_by_category = get_category_type_choices()
    categories = {}

    for category_code, category_label in Case.CaseCategory.choices:
        categories[category_code] = {
            "key": category_code,
            "label": category_label,
            "count": 0,
            "types": [
                {
                    "code": type_code,
                    "label": type_label,
                    "count": 0,
                }
                for type_code, type_label in type_choices_by_category.get(category_code, {}).items()
            ],
        }

    for case in cases:
        category_code = case.category or UNCATEGORIZED_CATEGORY_KEY
        if category_code not in categories:
            categories[category_code] = {
                "key": category_code,
                "label": UNCATEGORIZED_CATEGORY_LABEL,
                "count": 0,
                "types": [],
            }

        categories[category_code]["count"] += 1

        type_code = case.case_type_specific or UNTYPED_CASE_TYPE_KEY
        type_map = type_choices_by_category.get(category_code, {})
        type_label = type_map.get(type_code)
        if not type_label:
            type_label = case.get_specific_type_display() or UNTYPED_CASE_TYPE_LABEL

        type_entry = next(
            (
                item
                for item in categories[category_code]["types"]
                if item["code"] == type_code
            ),
            None,
        )
        if type_entry is None:
            type_entry = {
                "code": type_code,
                "label": type_label,
                "count": 0,
            }
            categories[category_code]["types"].append(type_entry)

        type_entry["count"] += 1

    categories_list = []
    for category in categories.values():
        if (
            category["key"] == UNCATEGORIZED_CATEGORY_KEY
            and category["count"] == 0
        ):
            continue

        category["types"] = sorted(category["types"], key=lambda item: item["label"])
        categories_list.append(category)

    return categories_list


class CaseNumberGenerator:
    """
    Genera números de caso únicos con 5 dígitos numéricos.
    """

    @staticmethod
    def generate_case_number() -> str:
        last_case = Case.objects.filter(
            case_number__regex=r'^\d{5}$'
        ).order_by('-case_number').first()

        if last_case:
            last_number = int(last_case.case_number)
            next_number = last_number + 1
        else:
            next_number = 1

        if next_number > 99999:
            raise ValueError("Se ha alcanzado el número máximo de casos (99999)")

        return str(next_number).zfill(5)


class CaseCompletionValidator:
    """
    Valida si un caso está completo para proceder con la asignación.
    """

    REQUIRED_DOCUMENTS = REQUIRED_CASE_DOCUMENT_TYPES

    @staticmethod
    def is_complete(case: Case) -> dict:
        result = {
            "is_complete": True,
            "missing_documents": [],
            "invalid_documents": [],
            "details": [],
        }

        if not case.title or not case.title.strip():
            result["is_complete"] = False
            result["details"].append("El caso no tiene título.")

        if not case.description or not case.description.strip():
            result["is_complete"] = False
            result["details"].append("El caso no tiene descripción.")

        if not case.beneficiary:
            result["is_complete"] = False
            result["details"].append("El caso no tiene beneficiario asignado.")

        case_documents = case.case_documents.all()
        documents_dict = {doc.document_type: doc for doc in case_documents}

        for doc_type in CaseCompletionValidator.REQUIRED_DOCUMENTS:
            doc_label = CaseDocument.DocumentType(doc_type).label

            if doc_type not in documents_dict:
                result["is_complete"] = False
                result["missing_documents"].append(doc_label)
                result["details"].append(f"Falta documento: {doc_label}")
            else:
                doc = documents_dict[doc_type]
                if not doc.is_valid:
                    result["is_complete"] = False
                    result["invalid_documents"].append(doc_label)
                    result["details"].append(f"Documento inválido: {doc_label}")

        return result

    @staticmethod
    def get_document_status(case: Case) -> dict:
        status = {
            "DOCUMENTO": {"exists": False, "valid": False},
            "RECIBO_SERVICIOS": {"exists": False, "valid": False},
            "FOTO": {"exists": False, "valid": False},
        }

        case_documents = case.case_documents.all()

        for doc in case_documents:
            if doc.document_type == CaseDocument.DocumentType.DOCUMENTO:
                key = "DOCUMENTO"
            elif doc.document_type == CaseDocument.DocumentType.RECIBO_SERVICIOS:
                key = "RECIBO_SERVICIOS"
            elif doc.document_type == CaseDocument.DocumentType.FOTO:
                key = "FOTO"
            else:
                continue

            status[key] = {
                "exists": True,
                "valid": doc.is_valid,
            }

        return status


class CaseDistributionService:
    """
    Servicio para gestionar el reparto (asignación) manual de casos.
    """

    @staticmethod
    def _get_review_responsible_student(case: Case) -> User | None:
        if case.assigned_student_id:
            return case.assigned_student

        interview_entry = (
            case.bitacora_entries
            .filter(entry_type=BitacoraEntry.EntryType.ENTREVISTA, author__role=User.Role.ESTUDIANTE)
            .select_related("author")
            .order_by("created_at")
            .first()
        )
        if interview_entry:
            return interview_entry.author

        workload_annotations = {
            "active_case_load": Count(
                "assigned_cases",
                filter=Q(assigned_cases__status__in=ACTIVE_ASSIGNED_CASE_STATUSES),
                distinct=True,
            ),
        }
        ordering = ["active_case_load", "id"]

        if case.category:
            workload_annotations["same_category_load"] = Count(
                "assigned_cases",
                filter=Q(
                    assigned_cases__category=case.category,
                    assigned_cases__status__in=ACTIVE_ASSIGNED_CASE_STATUSES,
                ),
                distinct=True,
            )
            ordering.insert(0, "same_category_load")

        return (
            User.objects
            .filter(role=User.Role.ESTUDIANTE, is_active=True)
            .annotate(**workload_annotations)
            .order_by(*ordering)
            .first()
        )

    @staticmethod
    def can_assign_case(case: Case, user: User) -> tuple[bool, str]:
        if user.role not in [User.Role.SECRETARIA, User.Role.ASESOR]:
            return False, "Solo Secretaría y Asesores pueden asignar casos."

        if case.status != Case.CaseStatus.SIN_ASIGNAR:
            current_status = case.get_status_display()
            return False, f"El caso debe estar sin asignar, actualmente está '{current_status}'."

        if case.assigned_student:
            return False, "El caso ya tiene un estudiante asignado."

        return True, ""

    @staticmethod
    @transaction.atomic
    def assign_case_manually(
            case: Case,
            student: User,
            category: str,
            case_type: str,
            assigned_by: User,
            notes: str = "",
    ) -> tuple[bool, str, CaseAssignment | None]:
        if student.role != User.Role.ESTUDIANTE:
            return False, "El usuario seleccionado no es un estudiante.", None

        if not student.is_active:
            return False, "El estudiante seleccionado no está activo.", None

        can_assign, reason = CaseDistributionService.can_assign_case(case, assigned_by)
        if not can_assign:
            return False, reason, None

        try:
            assignment = CaseAssignment.objects.create(
                case=case,
                assigned_student=student,
                assigned_advisor=assigned_by,
                assignment_type=CaseAssignment.AssignmentType.MANUAL,
                case_category=category,
                notes=notes,
            )

            case.assigned_student = student
            case.status = Case.CaseStatus.ASIGNADO
            case.category = category
            case.case_type_specific = case_type
            # Al asignar: etapa 1 se completa, ponemos etapa 2 como la activa
            case.current_stage = Case.CaseStage.INFORMATION_GATHERING

            case.save(
                update_fields=[
                    "assigned_student",
                    "status",
                    "category",
                    "case_type_specific",
                    "current_stage",
                    "updated_at",
                ]
            )

            bitacora_content = (
                f"Caso asignado manualmente a {student.full_name} "
                f"por {assigned_by.full_name}."
            )
            if notes:
                bitacora_content += f" Notas: {notes}"

            BitacoraEntry.objects.create(
                case=case,
                author=assigned_by,
                entry_type=BitacoraEntry.EntryType.CASO_ASIGNADO_MANUALMENTE,
                content=bitacora_content,
            )

            return True, "Caso asignado exitosamente.", assignment

        except Exception as e:
            logger.exception("Error al asignar caso manualmente.")
            return False, f"Error al asignar el caso: {str(e)}", None

    @staticmethod
    @transaction.atomic
    def send_to_review(
            case: Case,
            sent_by: User,
            reason: str = "",
    ) -> tuple[bool, str]:
        if sent_by.role not in [User.Role.SECRETARIA, User.Role.ASESOR]:
            return False, "Solo Secretaría y Asesores pueden enviar a revisión."

        if case.status != Case.CaseStatus.SIN_ASIGNAR:
            current_status = case.get_status_display()
            return False, f"El caso debe estar sin asignar, actualmente está '{current_status}'."

        try:
            review_student = CaseDistributionService._get_review_responsible_student(case)
            if not review_student:
                return False, "No hay estudiantes activos disponibles para autoasignar el caso en revisión."
            case.assigned_student = review_student
            case.status = Case.CaseStatus.AUTOASIGNADO
            case.current_stage = Case.CaseStage.INFORMATION_GATHERING
            case.save(update_fields=["assigned_student", "status", "current_stage", "updated_at"])

            bitacora_content = f"Caso enviado a revisión por {sent_by.full_name}."
            bitacora_content += (
                f" Quedó autoasignado a {review_student.full_name} "
                "para completar la documentación pendiente."
            )
            if reason:
                bitacora_content += f" Motivo: {reason}"

            BitacoraEntry.objects.create(
                case=case,
                author=sent_by,
                entry_type=BitacoraEntry.EntryType.CASO_ENVIADO_REVISION,
                content=bitacora_content,
            )

            return True, "Caso enviado a revisión exitosamente."

        except Exception as e:
            logger.exception("Error al enviar caso a revisión.")
            return False, f"Error al enviar el caso a revisión: {str(e)}"


class CaseDocumentService:
    """
    Servicio para gestionar documentos de los casos.
    """

    @staticmethod
    def get_required_documents_for_display(case: Case) -> dict:
        documents = {}
        status = CaseCompletionValidator.get_document_status(case)

        for doc_type in CaseCompletionValidator.REQUIRED_DOCUMENTS:
            if doc_type == CaseDocument.DocumentType.DOCUMENTO:
                doc_type_key = "DOCUMENTO"
            elif doc_type == CaseDocument.DocumentType.RECIBO_SERVICIOS:
                doc_type_key = "RECIBO_SERVICIOS"
            else:
                doc_type_key = "FOTO"

            doc_status = status.get(doc_type_key, {"exists": False, "valid": False})

            documents[doc_type_key] = {
                "exists": doc_status["exists"],
                "valid": doc_status["valid"],
            }

        return documents


class DelayedCasesDashboardService:
    """
    Clasifica casos activos segun fechas limite y rol del usuario.
    """

    RISK_WINDOW_DAYS = 3
    ACTIVE_STATUSES = [
        Case.CaseStatus.ASIGNADO,
        Case.CaseStatus.AUTOASIGNADO,
        Case.CaseStatus.EN_PROCESO,
        Case.CaseStatus.ESPERANDO_BENEFICIARIO,
        Case.CaseStatus.EN_REVISION,
    ]

    @classmethod
    def get_dashboard_data(cls, user: User) -> dict:
        now = timezone.now()
        risk_limit = now + timedelta(days=cls.RISK_WINDOW_DAYS)

        cases = cls.get_base_queryset(user).prefetch_related(
            Prefetch(
                "deadlines",
                queryset=CaseDeadline.objects.filter(is_completed=False).order_by("due_date"),
                to_attr="pending_deadlines",
            )
        )

        delayed_cases = []
        on_time_cases = []

        for case in cases:
            classified_case = cls._classify_case(case, now, risk_limit)
            if classified_case["is_delayed"]:
                delayed_cases.append(classified_case)
            else:
                on_time_cases.append(classified_case)

        delayed_cases.sort(key=lambda item: item["sort_date"] or now)
        on_time_cases.sort(key=lambda item: (item["sort_date"] is None, item["sort_date"] or now))

        return {
            "delayed_cases": delayed_cases,
            "on_time_cases": on_time_cases,
            "total_cases": len(delayed_cases) + len(on_time_cases),
            "delayed_count": len(delayed_cases),
            "on_time_count": len(on_time_cases),
            "risk_count": sum(1 for item in on_time_cases if item["is_at_risk"]),
            "risk_window_days": cls.RISK_WINDOW_DAYS,
        }

    @classmethod
    def get_base_queryset(cls, user: User):
        queryset = (
            Case.objects.filter(status__in=cls.ACTIVE_STATUSES)
            .select_related("beneficiary", "assigned_student", "advisor")
            .order_by("case_number")
        )

        if user.role == User.Role.ASESOR:
            return queryset.filter(advisor=user)

        if user.role == User.Role.ESTUDIANTE:
            return queryset.filter(assigned_student=user)

        if user.role == User.Role.SECRETARIA:
            return queryset

        return queryset.none()

    @classmethod
    def _classify_case(cls, case: Case, now, risk_limit) -> dict:
        pending_deadlines = list(getattr(case, "pending_deadlines", []))
        overdue_deadlines = [
            deadline for deadline in pending_deadlines if deadline.due_date < now
        ]

        if overdue_deadlines:
            primary_deadline = overdue_deadlines[0]
            days_delta = (now.date() - primary_deadline.due_date.date()).days
            return cls._build_case_row(
                case=case,
                primary_deadline=primary_deadline,
                is_delayed=True,
                is_at_risk=False,
                status_label="Retrasado",
                days_label=f"{days_delta} día(s) vencido",
                sort_date=primary_deadline.due_date,
            )

        primary_deadline = pending_deadlines[0] if pending_deadlines else None
        is_at_risk = bool(primary_deadline and primary_deadline.due_date <= risk_limit)

        if primary_deadline:
            days_delta = (primary_deadline.due_date.date() - now.date()).days
            if days_delta == 0:
                days_label = "Vence hoy"
            elif days_delta == 1:
                days_label = "Vence mañana"
            else:
                days_label = f"Vence en {days_delta} día(s)"
        else:
            days_label = "Sin fecha límite pendiente"

        return cls._build_case_row(
            case=case,
            primary_deadline=primary_deadline,
            is_delayed=False,
            is_at_risk=is_at_risk,
            status_label="En riesgo" if is_at_risk else "A tiempo",
            days_label=days_label,
            sort_date=primary_deadline.due_date if primary_deadline else None,
        )

    @staticmethod
    def _build_case_row(
        case: Case,
        primary_deadline: CaseDeadline | None,
        is_delayed: bool,
        is_at_risk: bool,
        status_label: str,
        days_label: str,
        sort_date,
    ) -> dict:
        return {
            "case": case,
            "primary_deadline": primary_deadline,
            "is_delayed": is_delayed,
            "is_at_risk": is_at_risk,
            "status_label": status_label,
            "days_label": days_label,
            "sort_date": sort_date,
            "pending_deadlines_count": len(getattr(case, "pending_deadlines", [])),
        }


class MissedAppointmentsDashboardService:
    """
    Construye el reporte de citas no atendidas segun rol del usuario.
    """

    @classmethod
    def get_dashboard_data(cls, user: User) -> dict:
        appointments = cls.get_base_queryset(user)
        no_show_appointments = []
        overdue_pending_appointments = []

        for appointment in appointments:
            item = cls._build_appointment_row(appointment)
            if item["classification_key"] == "no_show":
                no_show_appointments.append(item)
            else:
                overdue_pending_appointments.append(item)

        return {
            "no_show_appointments": no_show_appointments,
            "overdue_pending_appointments": overdue_pending_appointments,
            "total_missed": len(no_show_appointments) + len(overdue_pending_appointments),
            "no_show_count": len(no_show_appointments),
            "overdue_pending_count": len(overdue_pending_appointments),
        }

    @classmethod
    def get_base_queryset(cls, user: User):
        queryset = (
            CaseAppointment.objects.filter(scheduled_for__lt=timezone.now())
            .exclude(status=CaseAppointment.AppointmentStatus.ATTENDED)
            .select_related(
                "case",
                "case__beneficiary",
                "case__assigned_student",
                "case__advisor",
                "created_by",
            )
            .order_by("scheduled_for")
        )

        if user.role == User.Role.ASESOR:
            queryset = queryset.filter(case__advisor=user)
        elif user.role == User.Role.ESTUDIANTE:
            queryset = queryset.filter(case__assigned_student=user)
        elif user.role != User.Role.SECRETARIA:
            queryset = queryset.none()

        return queryset

    @staticmethod
    def _build_appointment_row(appointment: CaseAppointment) -> dict:
        if appointment.status == CaseAppointment.AppointmentStatus.NO_SHOW:
            classification_key = "no_show"
            classification_label = "No asistió"
        else:
            classification_key = "overdue_pending"
            classification_label = "Pendiente vencida"

        days_overdue = (timezone.now().date() - appointment.scheduled_for.date()).days

        if days_overdue == 0:
            overdue_label = "Venció hoy"
        elif days_overdue == 1:
            overdue_label = "1 día vencida"
        else:
            overdue_label = f"{days_overdue} días vencida"

        return {
            "appointment": appointment,
            "classification_key": classification_key,
            "classification_label": classification_label,
            "overdue_label": overdue_label,
        }


class CaseStageManager:
    """
    Gestiona el flujo de etapas del caso.

    Lógica de etapas:
      current_stage indica cuál etapa está EN PROGRESO.
      Toda etapa con número < current_stage aparece como COMPLETADA.
      Toda etapa con número > current_stage aparece como PENDIENTE.

    Mapeo estado → current_stage:
      SIN_ASIGNAR / DOCUMENTACION → 0  (ninguna etapa activa)
      ASIGNADO                    → 2  (etapa 1 completada, etapa 2 en progreso)
      EN_PROCESO                  → 3  (etapas 1-2 completadas, etapa 3 en progreso)
      ESPERANDO_BENEFICIARIO           → 3  (igual que EN_PROCESO)
      EN_REVISION                 → 4  (etapas 1-3 completadas, etapa 4 en progreso)
      CERRADO                     → 6  (todas completadas, 6 > max etapa 5)
    """

    @staticmethod
    def advance_to_stage_1(case: Case) -> None:
        """
        Avanza el caso a Etapa 2 (Recopilación), dejando la etapa 1 como completada.
        Se llama justo después de asignar un estudiante.
        """
        if case.current_stage < Case.CaseStage.INFORMATION_GATHERING:
            case.current_stage = Case.CaseStage.INFORMATION_GATHERING
            case.save(update_fields=["current_stage", "updated_at"])

    @staticmethod
    def calculate_current_stage(case: Case) -> int:
        """
        Calcula y devuelve el número de etapa activa según el estado del caso.
        """
        if case.status in [Case.CaseStatus.SIN_ASIGNAR, Case.CaseStatus.DOCUMENTACION]:
            return Case.CaseStage.UNASSIGNED                # 0 — ninguna activa

        if case.status in [Case.CaseStatus.ASIGNADO, Case.CaseStatus.AUTOASIGNADO]:
            return Case.CaseStage.INFORMATION_GATHERING     # 2 — etapa 1 ✓, etapa 2 en progreso

        if case.status == Case.CaseStatus.EN_PROCESO:
            return Case.CaseStage.ANALYSIS_DRAFTING         # 3 — etapas 1-2 ✓, etapa 3 en progreso

        if case.status == Case.CaseStatus.ESPERANDO_BENEFICIARIO:
            return Case.CaseStage.ANALYSIS_DRAFTING         # 3 — igual que EN_PROCESO

        if case.status == Case.CaseStatus.EN_REVISION:
            return Case.CaseStage.SUPERVISOR_REVIEW         # 4 — etapas 1-3 ✓, etapa 4 en progreso

        if case.status == Case.CaseStatus.CERRADO:
            return 6                                        # 6 > 5 — todas ✓ completadas

        return Case.CaseStage.UNASSIGNED                    # 0 — default

    @staticmethod
    def get_stage_display_info(case: Case) -> list:
        """
        Genera la lista de etapas con flags: active, completed, pending.
        Usado por el template case_detail.html.
        """
        current_stage = CaseStageManager.calculate_current_stage(case)
        is_closed = case.status == Case.CaseStatus.CERRADO

        stages = [
            {
                "number": Case.CaseStage.ASSIGNMENT,
                "title": Case.CaseStage.ASSIGNMENT.label,
                "active": current_stage == Case.CaseStage.ASSIGNMENT,
                "completed": is_closed or current_stage > Case.CaseStage.ASSIGNMENT,
            },
            {
                "number": Case.CaseStage.INFORMATION_GATHERING,
                "title": Case.CaseStage.INFORMATION_GATHERING.label,
                "active": current_stage == Case.CaseStage.INFORMATION_GATHERING,
                "completed": is_closed or current_stage > Case.CaseStage.INFORMATION_GATHERING,
            },
            {
                "number": Case.CaseStage.ANALYSIS_DRAFTING,
                "title": Case.CaseStage.ANALYSIS_DRAFTING.label,
                "active": current_stage == Case.CaseStage.ANALYSIS_DRAFTING,
                "completed": is_closed or current_stage > Case.CaseStage.ANALYSIS_DRAFTING,
            },
            {
                "number": Case.CaseStage.SUPERVISOR_REVIEW,
                "title": Case.CaseStage.SUPERVISOR_REVIEW.label,
                "active": current_stage == Case.CaseStage.SUPERVISOR_REVIEW,
                "completed": is_closed or current_stage > Case.CaseStage.SUPERVISOR_REVIEW,
            },
            {
                "number": Case.CaseStage.COURT_PRESENTATION,
                "title": Case.CaseStage.COURT_PRESENTATION.label,
                "active": current_stage == Case.CaseStage.COURT_PRESENTATION,
                "completed": is_closed or current_stage > Case.CaseStage.COURT_PRESENTATION,
            },
        ]

        return stages


def asignar_caso_automatico(caso_id: str, usuario_ejecutor: User) -> tuple[bool, str]:
    """
    Asigna un caso al estudiante con menor carga de trabajo.
    Solo debe ser ejecutado por usuarios con rol de Secretaría.
    """
    if usuario_ejecutor.role != User.Role.SECRETARIA:
        return False, "Error: Solo Secretaría puede ejecutar el reparto."

    try:
        caso = Case.objects.get(id=caso_id, status=Case.CaseStatus.SIN_ASIGNAR)
    except Case.DoesNotExist:
        return False, "El caso no existe o ya fue asignado."

    estudiantes_disponibles = (
        User.objects.filter(
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )
        .annotate(
            num_casos=Count(
                "assigned_cases",
                filter=Q(assigned_cases__status__in=ACTIVE_ASSIGNED_CASE_STATUSES),
            )
        )
        .filter(num_casos__lt=5)
        .order_by("num_casos", "first_name", "last_name")
    )

    estudiante_elegido = estudiantes_disponibles.first()

    if not estudiante_elegido:
        logger.warning("No hay estudiantes disponibles o todos llegaron al límite de 5 casos.")
        return False, "No hay estudiantes con cupo disponible en este momento."

    try:
        with transaction.atomic():
            CaseAssignment.objects.create(
                case=caso,
                assigned_student=estudiante_elegido,
                assigned_advisor=usuario_ejecutor,
                assignment_type=CaseAssignment.AssignmentType.AUTOMATIC,
                case_category=caso.category or "",
                notes="Asignación automática",
            )

            caso.assigned_student = estudiante_elegido
            caso.status = Case.CaseStatus.ASIGNADO
            # Etapa 1 completada, etapa 2 en progreso
            caso.current_stage = Case.CaseStage.INFORMATION_GATHERING
            caso.save(update_fields=["assigned_student", "status", "current_stage", "updated_at"])

            BitacoraEntry.objects.create(
                case=caso,
                author=usuario_ejecutor,
                entry_type=BitacoraEntry.EntryType.ASIGNACION,
                content=f"El sistema asignó automáticamente el caso a {estudiante_elegido.full_name}.",
            )

            logger.info(
                "Caso %s asignado automáticamente a %s",
                caso.id,
                estudiante_elegido.full_name,
            )
            return True, f"Caso asignado exitosamente a {estudiante_elegido.full_name}."

    except Exception as e:
        logger.exception("Error al asignar caso automáticamente.")
        return False, f"Error al asignar el caso: {str(e)}"


class CaseAutomaticDistributionService:
    """
    Servicio para distribuir automáticamente múltiples casos completos
    entre estudiantes de forma equitativa.
    """

    @staticmethod
    @transaction.atomic
    def ejecutar_reparto_automatico_masivo(
            executed_by: User,
    ) -> tuple[bool, str]:
        if executed_by.role not in [User.Role.SECRETARIA, User.Role.ASESOR]:
            return False, "Solo Secretaría y Asesores pueden ejecutar el reparto automático."

        casos_sin_asignar = Case.objects.filter(
            status=Case.CaseStatus.SIN_ASIGNAR
        ).select_related("beneficiary")

        casos_completos = []
        for caso in casos_sin_asignar:
            completion_check = CaseCompletionValidator.is_complete(caso)
            if completion_check["is_complete"]:
                casos_completos.append(caso)

        if not casos_completos:
            return False, "No hay casos completos sin asignar para distribuir."

        estudiantes = (
            User.objects.filter(
                role=User.Role.ESTUDIANTE,
                is_active=True,
            )
            .annotate(
                num_casos=Count(
                    "assigned_cases",
                    filter=Q(assigned_cases__status__in=ACTIVE_ASSIGNED_CASE_STATUSES),
                )
            )
            .order_by("num_casos", "first_name", "last_name")
        )

        if not estudiantes.exists():
            return False, "No hay estudiantes disponibles en el sistema."

        asignaciones_exitosas = 0
        errores = []

        for idx, caso in enumerate(casos_completos):
            estudiante_idx = idx % len(estudiantes)
            estudiante = estudiantes[estudiante_idx]

            try:
                CaseAssignment.objects.create(
                    case=caso,
                    assigned_student=estudiante,
                    assigned_advisor=executed_by,
                    assignment_type=CaseAssignment.AssignmentType.AUTOMATIC,
                    case_category=caso.category or "",
                    notes="Distribución automática equitativa",
                )

                caso.assigned_student = estudiante
                caso.status = Case.CaseStatus.ASIGNADO
                # Etapa 1 completada, etapa 2 en progreso
                caso.current_stage = Case.CaseStage.INFORMATION_GATHERING
                caso.save(
                    update_fields=[
                        "assigned_student",
                        "status",
                        "current_stage",
                        "updated_at",
                    ]
                )

                BitacoraEntry.objects.create(
                    case=caso,
                    author=executed_by,
                    entry_type=BitacoraEntry.EntryType.ASIGNACION,
                    content=f"Caso distribuido automáticamente a {estudiante.full_name}.",
                )

                asignaciones_exitosas += 1

            except Exception as e:
                logger.exception(f"Error al asignar caso {caso.id}")
                errores.append(f"Error en caso {caso.case_number}: {str(e)}")

        mensaje = f"Se distribuyeron exitosamente {asignaciones_exitosas} de {len(casos_completos)} casos."
        if errores:
            mensaje += f" Con {len(errores)} error(es)."
            logger.warning(f"Errores en reparto automático: {errores}")

        return True, mensaje
