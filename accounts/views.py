import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import TemplateView

from cases.models import Case, Notification, CaseDeadline
from .models import User
from cases.services import (
    DelayedCasesDashboardService,
    build_assigned_cases_category_summary,
    get_active_assigned_cases_queryset,
)
from .services import get_notifications_for_user, run_deadline_check, run_inactivity_check


def get_type_label(type_value):
    """Convierte el valor corto del trámite a su etiqueta completa."""
    if not type_value:
        return "Sin trámite"

    type_map = {
        # Sala Penal
        "PROC": "Proceso",
        "DER_PET": "Derecho de petición",
        "TUT": "Tutela",
        "CONC_DEN": "Concepto + denuncia",
        "CONC": "Concepto",
        "MEM": "Memorial",
        # Sala Laboral
        "LIQ": "Liquidación",
        "LIQ_CONC": "Liquidación + concepto",
        "QUE": "Queja",
        # Sala Civil
        "COB_PRE": "Cobro pre-jurídico",
        "CONC_DP": "Concepto + DP",
        "CLI_EMP": "Clínica empresarial",
        # Sala Familia
        # PROC, CONC_DP, DER_PET, TUT, MEM, QUE, COB_PRE, CONC ya están mapeados arriba
        # Sala Derecho Público - Migrantes
        "SOL_REF": "Solicitud de refugio",
        "SOL_REF_DP": "Solicitud de refugio + DP",
        "SOL_REF_TUT": "Solicitud de refugio + Tutela",
        "TRAM_SAL": "Trámite salvoconducto",
    }

    return type_map.get(type_value, type_value)


def get_topbar_user_data(user):
    return {
        "full_name": user.full_name,
        "role_name": user.get_role_display(),
        "initials": user.initials,
    }


class SplashView(TemplateView):
    template_name = "accounts/splash.html"

    def get(self, request, *args, **kwargs):
        return redirect("login")


class RoleSelectionView(TemplateView):
    template_name = "accounts/role_selection.html"

    def get(self, request, *args, **kwargs):
        return redirect("login")


class RoleLoginView(View):
    template_name = "accounts/login.html"

    ROLE_CONFIG = {
        "beneficiario": {
            "display_name": "Beneficiario/Usuario",
            "user_label": "Número de cédula",
            "user_placeholder": "Ingresa tu número de cédula",
            "icon": "beneficiario",
            "expected_role": User.Role.BENEFICIARIO,
        },
        "secretaria": {
            "display_name": "Secretaría",
            "user_label": "Número de documento",
            "user_placeholder": "Ingresa tu número de documento",
            "icon": "secretaria",
            "expected_role": User.Role.SECRETARIA,
        },
        "estudiante": {
            "display_name": "Estudiante",
            "user_label": "Número de documento",
            "user_placeholder": "Ingresa tu número de documento",
            "icon": "estudiante",
            "expected_role": User.Role.ESTUDIANTE,
        },
        "asesor": {
            "display_name": "Asesor",
            "user_label": "Número de documento",
            "user_placeholder": "Ingresa tu número de documento",
            "icon": "asesor",
            "expected_role": User.Role.ASESOR,
        },
    }

    def get_role_data(self):
        role = self.kwargs.get("role")
        role_data = self.ROLE_CONFIG.get(role, {
            "display_name": "Acceso al sistema",
            "user_label": "Número de documento",
            "user_placeholder": "Ingresa tu número de documento",
            "icon": "general",
        })
        return role, role_data

    def build_context(self):
        role, role_data = self.get_role_data()
        return {
            "role_key": role,
            "role_data": role_data,
            "user_label": role_data.get("user_label", "Número de documento"),
            "user_placeholder": role_data.get("user_placeholder", "Ingresa tu número de documento"),
        }

    def get(self, request, *args, **kwargs):
        role, role_data = self.get_role_data()
        if not role_data:
            messages.error(request, "Rol no válido.")
            return redirect("role_selection")
        return render(request, self.template_name, self.build_context())

    def post(self, request, *args, **kwargs):
        role, role_data = self.get_role_data()

        if not role_data:
            messages.error(request, "Rol no válido.")
            return redirect("role_selection")

        document_number = request.POST.get("document_number", "").strip()
        password = request.POST.get("password", "").strip()

        if not document_number or not password:
            messages.error(request, "Debes completar todos los campos.")
            return render(request, self.template_name, self.build_context())

        user = authenticate(
            request,
            document_number=document_number,
            password=password,
        )

        if user is None:
            messages.error(request, "Documento o contraseña incorrectos.")
            return render(request, self.template_name, self.build_context())

        login(request, user)
        return redirect("dashboard_redirect")


@method_decorator(login_required, name="dispatch")
class DashboardRedirectView(View):
    def get(self, request, *args, **kwargs):
        if request.user.role == User.Role.BENEFICIARIO:
            return redirect("beneficiary_dashboard")
        if request.user.role == User.Role.SECRETARIA:
            return redirect("secretary_dashboard")
        if request.user.role == User.Role.ESTUDIANTE:
            return redirect("student_dashboard")
        if request.user.role == User.Role.ASESOR:
            return redirect("advisor_dashboard")
        return redirect("splash")


@method_decorator(login_required, name="dispatch")
class BeneficiaryDashboardView(TemplateView):
    template_name = "accounts/beneficiary_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Role.BENEFICIARIO:
            return redirect("dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Mantengo la estructura demo original para no romper la UI existente
        context["beneficiary_data"] = {
            "full_name": "María González Pérez",
            "role_name": "Beneficiario/Usuario",
            "initials": "MG",
            "case_id": "12345",
            "process_stage": "En revisión de documentos",
            "assigned_student_name": "Carlos Ramírez",
            "assigned_student_program": "Estudiante de Derecho",
            "next_appointment": "28 de Febrero, 2026 - 2:00 PM",
            "start_date": "15 de Enero, 2026",
            "last_appointment_status": "No asistió",
            "last_appointment_date": "10 de Febrero, 2026",
            "next_appointment_title": "Revisión de caso",
            "assistant_url": "https://elevenlabs.io/app/talk-to?agent_id=agent_7401kc1tzgwae23r1jx4vwg53hrt&branch_id=agtbrch_4001kc9xrcq7e2wb914gezsma87x",
        }

        context["user_data"] = get_topbar_user_data(self.request.user)
        return context


@method_decorator(login_required, name="dispatch")
class BeneficiaryAppointmentsView(TemplateView):
    template_name = "accounts/beneficiary_appointments.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Role.BENEFICIARIO:
            return redirect("dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["beneficiary_data"] = {
            "full_name": "María González Pérez",
            "role_name": "Beneficiario/Usuario",
            "initials": "MG",
        }

        context["upcoming_appointments"] = [
            {
                "title": "Revisión de caso",
                "date": "28 de Febrero, 2026 - 2:00 PM",
                "with_person": "Carlos Ramírez",
                "status": "Pendiente",
            },
            {
                "title": "Preparación audiencia",
                "date": "15 de Marzo, 2026 - 10:00 AM",
                "with_person": "Carlos Ramírez",
                "status": "Pendiente",
            },
        ]

        context["past_appointments"] = [
            {
                "title": "Entrega documentos (Reprogramada)",
                "date": "20 de Febrero, 2026 - 3:00 PM",
                "with_person": "Carlos Ramírez",
                "notes": "Cliente entregó documentos faltantes. Todo en orden.",
                "status": "Asistió",
                "status_type": "success",
            },
            {
                "title": "Entrega documentos",
                "date": "10 de Febrero, 2026 - 11:00 AM",
                "with_person": "Carlos Ramírez",
                "notes": "Cliente no asistió. Se contactó vía telefónica para reprogramar.",
                "status": "No asistió",
                "status_type": "danger",
            },
            {
                "title": "Seguimiento",
                "date": "28 de Enero, 2026 - 2:00 PM",
                "with_person": "Carlos Ramírez",
                "notes": "Cliente entregó documentación solicitada. Se revisó avance del caso.",
                "status": "Asistió",
                "status_type": "success",
            },
            {
                "title": "Consulta inicial",
                "date": "15 de Enero, 2026 - 10:00 AM",
                "with_person": "Carlos Ramírez",
                "notes": "Primera consulta. Se explicó el proceso completo y se solicitó documentación inicial.",
                "status": "Asistió",
                "status_type": "success",
            },
        ]

        context["user_data"] = get_topbar_user_data(self.request.user)
        return context


@method_decorator(login_required, name="dispatch")
class SecretaryDashboardView(TemplateView):
    template_name = "accounts/secretary_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Role.SECRETARIA:
            return redirect("dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cases = Case.objects.select_related(
            "beneficiary",
            "assigned_student"
        ).all().order_by("-updated_at")

        context["user_data"] = get_topbar_user_data(self.request.user)
        context["total_cases"] = cases.count()
        assigned_cases = get_active_assigned_cases_queryset().select_related(
            "beneficiary",
            "assigned_student",
        )

        context["unassigned_cases"] = cases.filter(
            status=Case.CaseStatus.SIN_ASIGNAR
        ).count()
        context["assigned_cases"] = assigned_cases.count()
        
        # Contar casos cerrados por tipo
        closed_cases_total = cases.filter(status=Case.CaseStatus.CERRADO).count()

        def count_closed(closure_type):
            return cases.filter(status=Case.CaseStatus.CERRADO, closure_type=closure_type).count()

        context["closed_cases"]       = closed_cases_total
        context["closed_des_tac"]     = count_closed(Case.ClosureType.DESISTIMIENTO_TACITO)
        context["closed_des_exp"]     = count_closed(Case.ClosureType.DESISTIMIENTO_EXPRESO)
        context["closed_fin_gan"]     = count_closed(Case.ClosureType.FINALIZADO_GANADO)
        context["closed_fin_per"]     = count_closed(Case.ClosureType.FINALIZADO_PERDIDO)
        context["closed_inf_ter"]     = count_closed(Case.ClosureType.INFRINGIO_TERMINOS)

        closed_summary = []
        for process_code, process_label in Case.ClosureProcessType.choices:
            outcomes = []
            process_total = 0
            for outcome_code, outcome_label in Case.ClosureType.choices:
                outcome_count = cases.filter(
                    status=Case.CaseStatus.CERRADO,
                    closure_process_type=process_code,
                    closure_type=outcome_code,
                ).count()
                process_total += outcome_count
                outcomes.append({
                    "code": outcome_code,
                    "label": outcome_label,
                    "count": outcome_count,
                })

            closed_summary.append({
                "code": process_code,
                "label": process_label,
                "count": process_total,
                "outcomes": outcomes,
            })

        context["closed_summary"] = closed_summary
        context["recent_cases"] = cases
        delayed_dashboard = DelayedCasesDashboardService.get_dashboard_data(self.request.user)
        context["delayed_cases_count"] = delayed_dashboard["delayed_count"]
        context["delayed_cases_preview"] = delayed_dashboard["delayed_cases"][:5]
        context["delayed_cases_total_active"] = delayed_dashboard["total_cases"]

        # NO hacer json.dumps() - dejar que json_script lo maneje
        context["categories_json"] = build_assigned_cases_category_summary(assigned_cases)

        return context


@method_decorator(login_required, name="dispatch")
class StudentDashboardView(TemplateView):
    template_name = "accounts/student_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Role.ESTUDIANTE:
            return redirect("dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        case_obj = (
            Case.objects.select_related("beneficiary", "advisor")
            .filter(assigned_student=self.request.user)
            .order_by("-updated_at")
            .first()
        )

        assigned_cases_count = Case.objects.filter(
            assigned_student=self.request.user
        ).count()

        context["user_data"] = get_topbar_user_data(self.request.user)
        context["assigned_case"] = case_obj
        context["assigned_cases_count"] = assigned_cases_count
        context["alerts"] = [
            {
                "title": "Audiencia",
                "text": "Audiencia de divorcio y custodia - Juzgado Familia",
                "date": "24 de febrero de 2026",
                "type": "danger",
            },
            {
                "title": "Entrega Documentos",
                "text": "Presentar documentación complementaria al juzgado",
                "date": "1 de marzo de 2026",
                "type": "warning",
            },
            {
                "title": "Vencimiento",
                "text": "Fecha límite para responder solicitud de información",
                "date": "8 de marzo de 2026",
                "type": "success",
            },
            {
                "title": "Cita Cliente",
                "text": "Reunión seguimiento con beneficiaria",
                "date": "13 de marzo de 2026",
                "type": "success",
            },
        ]
        context["latest_notes"] = [
            "Cliente aportó certificado de matrimonio y actas de nacimiento de los hijos.",
            "Primera entrevista realizada. Cliente solicita custodia compartida.",
        ]
        return context


@method_decorator(login_required, name="dispatch")
class AdvisorDashboardView(TemplateView):
    template_name = "accounts/advisor_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Role.ASESOR:
            return redirect("dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        supervised_cases = Case.objects.filter(advisor=self.request.user).count()
        delayed_dashboard = DelayedCasesDashboardService.get_dashboard_data(self.request.user)

        context["user_data"] = get_topbar_user_data(self.request.user)
        context["supervised_cases"] = supervised_cases
        context["students_count"] = User.objects.filter(role=User.Role.ESTUDIANTE).count()
        context["cases_on_time"] = delayed_dashboard["on_time_count"]
        context["delayed_cases"] = delayed_dashboard["delayed_count"]
        context["risk_cases"] = delayed_dashboard["risk_count"]
        context["alerts"] = delayed_dashboard["delayed_cases"][:3]
        return context


@method_decorator(login_required, name="dispatch")
class NotificationsCenterView(TemplateView):
    template_name = "accounts/notifications_center.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        run_inactivity_check()
        run_deadline_check()

        can_view_advisor_notifications = self.request.user.role == User.Role.ASESOR

        all_notifications = Notification.objects.filter(
            recipient=self.request.user,
            is_resolved=False
        ).select_related("case", "deadline", "related_document", "related_entry").order_by("-created_at")

        if not can_view_advisor_notifications:
            all_notifications = all_notifications.exclude(
                notification_type__in=[
                    Notification.NotificationType.DOCUMENT_UPLOAD,
                    Notification.NotificationType.IMPORTANT_EVENT,
                ]
            )

        inactivity_notifications = all_notifications.filter(
            notification_type=Notification.NotificationType.INACTIVITY
        )

        document_notifications = all_notifications.filter(
            notification_type=Notification.NotificationType.DOCUMENT_UPLOAD
        )

        deadline_notifications = all_notifications.filter(
            notification_type=Notification.NotificationType.DEADLINE
        )

        info_notifications = all_notifications.filter(
            notification_type=Notification.NotificationType.INFO
        )

        event_notifications = all_notifications.filter(
            notification_type=Notification.NotificationType.IMPORTANT_EVENT
        )

        alert_notifications = all_notifications.filter(
            notification_type__in=[
                Notification.NotificationType.DEADLINE,
                Notification.NotificationType.INFO,
            ]
        )

        context["user_data"] = get_topbar_user_data(self.request.user)
        context["can_view_advisor_notifications"] = can_view_advisor_notifications
        context["can_view_document_notifications"] = can_view_advisor_notifications
        context["all_notifications"] = all_notifications
        context["inactivity_notifications"] = inactivity_notifications
        context["document_notifications"] = document_notifications
        context["deadline_notifications"] = deadline_notifications
        context["info_notifications"] = info_notifications
        context["event_notifications"] = event_notifications
        context["alert_notifications"] = alert_notifications
        context["total_notifications"] = all_notifications.count()
        context["total_inactivity"] = inactivity_notifications.count()
        context["total_documents"] = document_notifications.count()
        context["total_deadlines"] = deadline_notifications.count()
        context["total_info"] = info_notifications.count()
        context["total_events"] = event_notifications.count()
        context["total_alerts"] = alert_notifications.count()

        return context

class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("splash")


def get_topbar_user_data(user):
    return {
        "full_name": user.full_name,
        "role_name": user.get_role_display(),
        "initials": user.initials,
    }


class PasswordResetRequestView(View):
    def get(self, request):
        return render(request, 'accounts/password_reset_request.html')

    def post(self, request):
        document_number = request.POST.get('document_number', '').strip()
        email = request.POST.get('email', '').strip()

        if document_number and email:
            try:
                user = User.objects.get(document_number=document_number)
                print(f'[RESET] Usuario encontrado: {user.document_number}')
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )

                html_message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                })

                try:
                    send_mail(
                        subject='Restablecer contraseña — Consultorio Jurídico',
                        message=f'Haz clic en el siguiente enlace para restablecer tu contraseña: {reset_url}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    print(f'[RESET] Correo enviado a: {email}')
                except Exception as e:
                    print(f'[RESET] ERROR al enviar correo: {repr(e)}')

            except User.DoesNotExist:
                print(f'[RESET] Usuario NO encontrado con documento: {document_number}')

        else:
            print(f'[RESET] Campos vacíos - documento: "{document_number}" email: "{email}"')

        return render(request, 'accounts/password_reset_request.html', {'sent': True})


class PasswordResetConfirmView(View):
    def _get_user(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if PasswordResetTokenGenerator().check_token(user, token):
                return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        return None

    def get(self, request, uidb64, token):
        user = self._get_user(uidb64, token)
        if not user:
            return render(request, 'accounts/password_reset_confirm.html', {'invalid': True})
        return render(request, 'accounts/password_reset_confirm.html', {
            'uidb64': uidb64, 'token': token,
        })

    def post(self, request, uidb64, token):
        user = self._get_user(uidb64, token)
        if not user:
            return render(request, 'accounts/password_reset_confirm.html', {'invalid': True})

        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            return render(request, 'accounts/password_reset_confirm.html', {
                'uidb64': uidb64, 'token': token,
                'error': 'La contraseña debe tener al menos 8 caracteres.',
            })
        if password1 != password2:
            return render(request, 'accounts/password_reset_confirm.html', {
                'uidb64': uidb64, 'token': token,
                'error': 'Las contraseñas no coinciden.',
            })

        user.set_password('Icesi2026*')
        user.save()
        return redirect('password_reset_complete')


class PasswordResetCompleteView(View):
    def get(self, request):
        return render(request, 'accounts/password_reset_complete.html')
