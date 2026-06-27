from unittest import case

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Case(models.Model):
    """
    Modelo principal del caso jurídico.
    Conserva campos de compatibilidad con versiones anteriores
    y agrega los nuevos necesarios para el sprint.
    """

    class CaseCategory(models.TextChoices):
        PENAL = "PEN", "Sala Penal"
        LABORAL = "LAB", "Sala Laboral"
        CIVIL = "CIV", "Sala Civil"
        FAMILIA = "FAM", "Sala Familia"
        DERECHO_PUBLICO_MIGRANTES = "DER_PUB_MIG", "Sala Derecho Público"
        PUBLICO = "PUB", "Sala derecho público"
        PUBLICO_MIGRANTES = "MIGR", "Sala derecho público - Migrantes"
        ADMINISTRATIVO = "ADM", "Sala administrativa"

    class PenalType(models.TextChoices):
        PROCESO = "PROC", "Proceso"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        TUTELA = "TUT", "Tutela"
        CONCEPTO_DENUNCIA = "CONC_DEN", "Concepto + denuncia"
        CONCEPTO = "CONC", "Concepto"
        MEMORIAL = "MEM", "Memorial"
        DERECHO_FISCAL = "DER_FIS", "Derecho fiscal"
        DERECHO_DISCIPLINARIO = "DER_DIS", "Derecho disciplinario"

    class PublicoType(models.TextChoices):
        PROCESO = "PROC", "Proceso"
        CONCEPTO_DP = "CONC_DP", "Concepto + DP"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        TUTELA = "TUT", "Tutela"
        MEMORIAL = "MEM", "Memorial"
        QUEJA = "QUE", "Queja"
        COBRO_PREJURIDICO = "COB_PRE", "Cobro pre-jurídico"
        CONCEPTO = "CONC", "Concepto"
        MIGRANTES = "MIG", "Migrantes"
        DERECHO_ADMINISTRATIVO = "DER_ADM", "Derecho Administrativo y constitucional"

    class LaboralType(models.TextChoices):
        PROCESO = "PROC", "Proceso"
        LIQUIDACION = "LIQ", "Liquidación"
        LIQUIDACION_CONCEPTO = "LIQ_CONC", "Liquidación + concepto"
        TUTELA = "TUT", "Tutela"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        CONCEPTO = "CONC", "Concepto"
        QUEJA = "QUE", "Queja"
        MEMORIAL = "MEM", "Memorial"

    class CivilType(models.TextChoices):
        PROCESO = "PROC", "Proceso"
        COBRO_PREJURIDICO = "COB_PRE", "Cobro pre-jurídico"
        TUTELA = "TUT", "Tutela"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        CONCEPTO_DP = "CONC_DP", "Concepto + DP"
        QUEJA = "QUE", "Queja"
        MEMORIAL = "MEM", "Memorial"
        CONCEPTO = "CONC", "Concepto"
        CLINICA_EMPRESARIAL = "CLI_EMP", "Clínica empresarial"

    class FamiliaType(models.TextChoices):
        PROCESO = "PROC", "Proceso"
        CONCEPTO_DP = "CONC_DP", "Concepto + DP"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        TUTELA = "TUT", "Tutela"
        MEMORIAL = "MEM", "Memorial"
        QUEJA = "QUE", "Queja"
        COBRO_PREJURIDICO = "COB_PRE", "Cobro pre-jurídico"
        CONCEPTO = "CONC", "Concepto"

    class PublicoMigrantesType(models.TextChoices):
        SOLICITUD_REFUGIO = "SOL_REF", "Solicitud de refugio"
        SOLICITUD_REFUGIO_DP = "SOL_REF_DP", "Solicitud de refugio + DP"
        SOLICITUD_REFUGIO_TUTELA = "SOL_REF_TUT", "Solicitud de refugio + Tutela"
        TRAMITE_SALVOCONDUCTO = "TRAM_SAL", "Trámite salvoconducto"
        TUTELA = "TUT", "Tutela"
        CONCEPTO_DP = "CONC_DP", "Concepto + DP"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        CONCEPTO = "CONC", "Concepto"

    class DerechoPublicoMigrantesType(models.TextChoices):
        SOLICITUD_REFUGIO = "SOL_REF", "Solicitud de refugio"
        SOLICITUD_REFUGIO_DP = "SOL_REF_DP", "Solicitud de refugio + DP"
        SOLICITUD_REFUGIO_TUT = "SOL_REF_TUT", "Solicitud de refugio + Tutela"
        TRAMITE_SALVOCONDUCTO = "TRAM_SAL", "Trámite salvoconducto"
        TUTELA = "TUT", "Tutela"
        CONCEPTO_DP = "CONC_DP", "Concepto + DP"
        DERECHO_PETICION = "DER_PET", "Derecho de petición"
        CONCEPTO = "CONC", "Concepto"

    class CaseStatus(models.TextChoices):
        SIN_ASIGNAR = "SIN", "Sin asignar"
        DOCUMENTACION = "DOC", "Documentación"
        ASIGNADO = "ASI", "Asignado"
        AUTOASIGNADO = "AUT", "Autoasignado"
        EN_PROCESO = "PRO", "En proceso"
        ESPERANDO_BENEFICIARIO = "ESP", "Esperar por beneficiario"
        EN_REVISION = "REV", "En revisión"
        CERRADO = "CER", "Cerrado"

    class CaseStage(models.IntegerChoices):
        UNASSIGNED = 0, "Sin asignar"
        ASSIGNMENT = 1, "Asignación de Estudiante"
        INFORMATION_GATHERING = 2, "Recopilación de Información"
        ANALYSIS_DRAFTING = 3, "Análisis y Redacción"
        SUPERVISOR_REVIEW = 4, "Revisión con Supervisor"
        COURT_PRESENTATION = 5, "Presentación ante Juzgado"

    class ClosureType(models.TextChoices):
        DESISTIMIENTO_TACITO   = "DES_TAC", "Desistimiento tácito del usuario"
        DESISTIMIENTO_EXPRESO  = "DES_EXP", "Desistimiento expreso del usuario"
        FINALIZADO_GANADO      = "FIN_GAN", "Caso finalizado jurídicamente (Ganado)"
        FINALIZADO_PERDIDO     = "FIN_PER", "Caso finalizado (perdido)"
        INFRINGIO_TERMINOS     = "INF_TER", "Infringió los términos del consultorio jurídico"
        FAVORABLE = "FAV", "A favor"
        NEGATIVE = "NEG", "En contra"
        DISMISSED = "DIS", "Desistido"

    class ClosureProcessType(models.TextChoices):
        TUTELA = "TUT", "Tutela"
        JUDICIAL_PROCESS = "PRO", "Proceso judicial"

    class ClosureReason(models.TextChoices):
        DESISTIMIENTO_TACITO = "DES_TAC", "Desistimiento tácito del usuario"
        DESISTIMIENTO_EXPRESO = "DES_EXP", "Desistimiento expreso del usuario"
        GANADO = "GAN", "Caso finalizado jurídicamente (ganado)"
        PERDIDO = "PER", "Caso finalizado jurídicamente (perdido)"
        INFRINGIO_TERMINOS = "INF_TER", "Infringió los términos del consultorio jurídico"

    case_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de caso",
    )

    sequence_number = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Número secuencial",
        help_text="Número de orden del caso (1, 2, 3, ...)",
    )

    beneficiary = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="beneficiary_cases",
        verbose_name="Beneficiario",
    )

    assigned_student = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
        verbose_name="Estudiante asignado",
    )

    advisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advisor_cases",
        verbose_name="Asesor",
    )

    secretary = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_cases",
        verbose_name="Secretaría",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="Título",
    )

    description = models.TextField(
        verbose_name="Descripción",
    )

    # Nueva estructura usada por reparto/manual/filtros
    category = models.CharField(
        max_length=20,
        choices=CaseCategory.choices,
        null=True,
        blank=True,
        verbose_name="Sala",
    )

    case_type_specific = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Trámite jurídico",
    )

    status = models.CharField(
        max_length=10,
        choices=CaseStatus.choices,
        default=CaseStatus.SIN_ASIGNAR,
        verbose_name="Estado",
    )

    current_stage = models.IntegerField(
        choices=CaseStage.choices,
        default=CaseStage.UNASSIGNED,
        verbose_name="Etapa actual del caso",
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Teléfono",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Dirección",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    closure_type = models.CharField(
        max_length=10,
        choices=ClosureType.choices,
        null=True,
        blank=True,
        verbose_name="Tipo de cierre",
        help_text="Solo se llena cuando el caso se cierra",
    )
    closure_process_type = models.CharField(
        max_length=3,
        choices=ClosureProcessType.choices,
        default=ClosureProcessType.JUDICIAL_PROCESS,
        verbose_name="Tipo de asunto de cierre",
    )
    closure_reason = models.CharField(
        max_length=10,
        choices=ClosureReason.choices,
        null=True,
        blank=True,
        verbose_name="Motivo de cierre",
    )

    closure_description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descripción del cierre",
        help_text="Descripción detallada del motivo de cierre",
    )

    class Meta:
        verbose_name = "Caso"
        verbose_name_plural = "Casos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Caso {self.case_number}"

    def get_specific_type_display(self):
        """
        Devuelve una etiqueta legible del trámite jurídico según la sala.
        Esto ayuda a vistas y templates.
        """
        if not self.case_type_specific:
            return ""

        mapping = {
            self.CaseCategory.PENAL: dict(self.PenalType.choices),
            self.CaseCategory.LABORAL: dict(self.LaboralType.choices),
            self.CaseCategory.CIVIL: dict(self.CivilType.choices),
            self.CaseCategory.FAMILIA: dict(self.FamiliaType.choices),
            self.CaseCategory.DERECHO_PUBLICO_MIGRANTES: dict(self.DerechoPublicoMigrantesType.choices),
            self.CaseCategory.PUBLICO_MIGRANTES: dict(self.PublicoMigrantesType.choices),
        }

        category_choices = mapping.get(self.category, {})
        return category_choices.get(self.case_type_specific, self.case_type_specific)

    def get_category_full_name(self):
        """
        Devuelve el nombre completo de la sala/categoría.
        Garantiza que siempre se muestre el nombre completo sin abreviaciones.
        """
        category_map = {
            self.CaseCategory.PENAL: "Sala Penal",
            self.CaseCategory.LABORAL: "Sala Laboral",
            self.CaseCategory.CIVIL: "Sala Civil",
            self.CaseCategory.FAMILIA: "Sala Familia",
            self.CaseCategory.DERECHO_PUBLICO_MIGRANTES: "Sala Derecho Público",
        }
        return category_map.get(self.category, self.get_category_display())

    def save(self, *args, **kwargs):
        """
        Genera automáticamente el case_number si no existe.
        """
        if not self.case_number:
            from .services import CaseNumberGenerator
            self.case_number = CaseNumberGenerator.generate_case_number()
        
        super().save(*args, **kwargs)


class BitacoraEntry(models.Model):
    """
    Entradas de seguimiento del caso.
    Reemplaza la lógica vieja de Binnacle.
    """

    class EntryType(models.TextChoices):
        ACTUALIZACION = "ACT", "Actualización"
        ENTREVISTA = "ENT", "Entrevista"
        OBSERVACION = "OBS", "Observación"
        ASIGNACION = "ASI", "Asignación"
        DOCUMENTO = "DOC", "Documento"
        EVENTO = "EVE", "Evento"
        CASO_ASIGNADO_MANUALMENTE = "CAS_MAN", "Caso Asignado Manualmente"
        CASO_ENVIADO_REVISION = "CAS_REV", "Caso Enviado a Revisión"

    class EventType(models.TextChoices):
        SEGUIMIENTO = "SEG", "Seguimiento del caso"
        REUNION = "REU", "Reunión"
        AUDIENCIA = "AUD", "Audiencia"
        TRIBUNAL = "TRI", "Cita de tribunal"
        VENCIMIENTO = "VEN", "Vencimiento de término"
        DOCUMENTO = "DOC", "Documento o soporte"
        OTRO = "OTR", "Otro evento"

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="bitacora_entries",
        verbose_name="Caso",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bitacora_entries",
        verbose_name="Autor",
    )

    entry_type = models.CharField(
        max_length=10,
        choices=EntryType.choices,
        default=EntryType.EVENTO,
        verbose_name="Clasificación interna",
    )

    event_type = models.CharField(
        max_length=3,
        choices=EventType.choices,
        default=EventType.SEGUIMIENTO,
        verbose_name="Tipo de evento",
    )

    content = models.TextField(
        verbose_name="Contenido",
    )

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha del evento",
    )

    notify = models.BooleanField(
        default=False,
        verbose_name="Enviar notificación por correo",
    )

    starts_new_term = models.BooleanField(
        default=False,
        verbose_name="Empezar a contar nuevo término",
    )

    term_due_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y hora de vencimiento del término",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    class Meta:
        verbose_name = "Entrada de Bitácora"
        verbose_name_plural = "Entradas de Bitácora"
        ordering = ["-created_at"]

    def clean(self):
        now = timezone.now()

        if self.scheduled_for:
            scheduled = self.scheduled_for
            if timezone.is_naive(scheduled):
                scheduled = timezone.make_aware(scheduled)
            if scheduled < now:
                raise ValidationError("La fecha programada no puede estar en el pasado.")

        if self.term_due_at:
            term = self.term_due_at
            if timezone.is_naive(term):
                term = timezone.make_aware(term)
            if term < now:
                raise ValidationError("La fecha de vencimiento del término no puede estar en el pasado.")

        if self.starts_new_term and not self.term_due_at:
            raise ValidationError("Debes indicar la fecha y hora de vencimiento del nuevo término.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def author_initials(self):
        try:
            return self.author.initials
        except AttributeError:
            first = getattr(self.author, "first_name", "") or ""
            last = getattr(self.author, "last_name", "") or ""
            initials = f"{first[:1]}{last[:1]}".upper()
            return initials or "US"

    @property
    def author_role(self):
        try:
            return self.author.get_role_display()
        except AttributeError:
            return "Usuario"

    def __str__(self):
        return f"Bitácora {self.id} - Caso {self.case.case_number}"


class BitacoraDocument(models.Model):
    """
    Archivos adjuntos a una entrada de bitácora.
    """

    entry = models.ForeignKey(
        BitacoraEntry,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Entrada de bitácora",
    )

    file = models.FileField(
        upload_to="bitacora_documents/%Y/%m/%d/",
        verbose_name="Archivo",
    )

    original_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nombre original",
    )

    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tamaño del archivo",
    )

    content_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Tipo MIME",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de subida",
    )

    class Meta:
        verbose_name = "Documento de Bitácora"
        verbose_name_plural = "Documentos de Bitácora"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_name or self.file.name

    def save(self, *args, **kwargs):
        if self.file:
            if not self.original_name:
                self.original_name = self.file.name
            if not self.file_size:
                try:
                    self.file_size = self.file.size
                except Exception:
                    pass
            if not self.content_type:
                self.content_type = getattr(self.file, "content_type", None)
        super().save(*args, **kwargs)


class CaseDocument(models.Model):
    """
    Documentos requeridos para reparto/validación del caso.
    """

    class DocumentType(models.TextChoices):
        DOCUMENTO = "DOC", "Documento"
        RECIBO_SERVICIOS = "REC", "Recibo de Servicios"
        FOTO = "FOT", "Foto"

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="case_documents",
        verbose_name="Caso",
    )

    document_type = models.CharField(
        max_length=3,
        choices=DocumentType.choices,
        verbose_name="Tipo de Documento",
    )

    file = models.FileField(
        upload_to="case_documents/%Y/%m/%d/",
        verbose_name="Archivo",
    )

    original_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nombre original",
    )

    is_valid = models.BooleanField(
        default=True,
        verbose_name="Válido",
    )

    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tamaño del archivo",
    )

    content_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Tipo MIME",
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_documents_uploaded",
        verbose_name="Subido por",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de subida",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Documento de Caso"
        verbose_name_plural = "Documentos de Caso"
        ordering = ["-uploaded_at"]
        unique_together = [["case", "document_type"]]

    def __str__(self):
        return f"{self.get_document_type_display()} - Caso {self.case.case_number}"

    def save(self, *args, **kwargs):
        if self.file:
            if not self.original_name:
                self.original_name = self.file.name
            if not self.file_size:
                try:
                    self.file_size = self.file.size
                except Exception:
                    pass
            if not self.content_type:
                try:
                    self.content_type = self.file.file.content_type
                except Exception:
                    pass
        super().save(*args, **kwargs)

class CaseAssignment(models.Model):
    """
    Historial de asignaciones del caso.
    No reemplaza el assigned_student del caso; lo complementa para trazabilidad.
    """

    class AssignmentType(models.TextChoices):
        MANUAL = "MAN", "Manual"
        AUTOMATIC = "AUTO", "Automática"

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Caso",
    )

    assigned_student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="student_assignments",
        verbose_name="Estudiante asignado",
    )

    assigned_advisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="advisor_assignments",
        verbose_name="Asesor o asignador",
    )

    assignment_type = models.CharField(
        max_length=4,
        choices=AssignmentType.choices,
        default=AssignmentType.MANUAL,
        verbose_name="Tipo de asignación",
    )

    case_category = models.CharField(
        max_length=20,
        choices=Case.CaseCategory.choices,
        verbose_name="Sala del caso",
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de asignación",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
    )

    class Meta:
        verbose_name = "Asignación de Caso"
        verbose_name_plural = "Asignaciones de Caso"
        ordering = ["-assigned_at"]

    def __str__(self):
        student_name = getattr(self.assigned_student, "full_name", str(self.assigned_student))
        return f"Caso {self.case.case_number} → {student_name}"


class CaseDeadline(models.Model):
    """
    Fechas límite asociadas a un caso.
    """
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="deadlines",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_deadlines",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date"]
        verbose_name = "Fecha límite"
        verbose_name_plural = "Fechas límite"

    def __str__(self):
        return f"{self.title} - {self.case.case_number}"

    @property
    def is_overdue(self):
        return not self.is_completed and self.due_date < timezone.now()

    @property
    def is_due_soon(self):
        if self.is_completed:
            return False
        delta = self.due_date - timezone.now()
        return 0 <= delta.days <= 2


class CaseAppointment(models.Model):
    """
    Citas asociadas a un caso.
    Permite reportar citas vencidas que no fueron atendidas.
    """

    class AppointmentStatus(models.TextChoices):
        PENDING = "PEN", "Pendiente"
        ATTENDED = "ATE", "Atendida"
        NO_SHOW = "NAS", "No asistió"
        RESCHEDULED = "REP", "Reprogramada"
        CANCELLED = "CAN", "Cancelada"

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Caso",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Título de la cita",
    )
    scheduled_for = models.DateTimeField(
        verbose_name="Fecha y hora de la cita",
    )
    status = models.CharField(
        max_length=3,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        verbose_name="Estado",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
        verbose_name="Creada por",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        ordering = ["scheduled_for"]
        verbose_name = "Cita de caso"
        verbose_name_plural = "Citas de caso"

    def __str__(self):
        return f"{self.title} - Caso {self.case.case_number}"

    @property
    def is_missed(self):
        return self.scheduled_for < timezone.now() and self.status != self.AppointmentStatus.ATTENDED

    @property
    def missed_classification(self):
        if self.status == self.AppointmentStatus.NO_SHOW:
            return "No asistió"
        return "Pendiente vencida"


class CaseCalendarEvent(models.Model):
    class EventType(models.TextChoices):
        REUNION = "REU", "Reunión"
        ENTREGA = "ENT", "Entrega"
        CITA = "CIT", "Cita"
        PRESENTACION = "PRE", "Presentación ante Juzgado"
        OTRO = "OTR", "Otro"

    _COLORS = {
        "REU": "#5454e8",
        "ENT": "#f59e0b",
        "CIT": "#10b981",
        "PRE": "#ef4444",
        "OTR": "#6b7280",
    }

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="calendar_events")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_calendar_events"
    )
    event_type = models.CharField(max_length=3, choices=EventType.choices, default=EventType.REUNION)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=False)
    teams_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_datetime"]
        verbose_name = "Evento del calendario"
        verbose_name_plural = "Eventos del calendario"

    def __str__(self):
        return f"{self.title} — Caso {self.case.case_number}"

    @property
    def color(self):
        return self._COLORS.get(self.event_type, "#6b7280")


class AdvisorAvailabilitySlot(models.Model):
    advisor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="availability_slots"
    )
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="availability_slots")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    booked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="booked_slots"
    )
    teams_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_datetime"]
        verbose_name = "Franja de disponibilidad"
        verbose_name_plural = "Franjas de disponibilidad"

    def __str__(self):
        return f"Disponibilidad {self.advisor.full_name} — {self.start_datetime.strftime('%d/%m/%Y %H:%M')}"


class Notification(models.Model):
    """
    Notificaciones del sistema.
    """

    class NotificationType(models.TextChoices):
        INACTIVITY = "INA", "Inactividad"
        DEADLINE = "DEA", "Fecha límite"
        INFO = "INF", "Informativa"
        DOCUMENT_UPLOAD = "DOC", "Documento subido"
        IMPORTANT_EVENT = "EVE", "Evento importante"

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    deadline = models.ForeignKey(
        CaseDeadline,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    related_document = models.ForeignKey(
        BitacoraDocument,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    related_entry = models.ForeignKey(
        BitacoraEntry,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        max_length=3,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "related_document", "notification_type"],
                name="unique_notification_per_bitacora_document",
            ),
            models.UniqueConstraint(
                fields=["recipient", "related_entry", "notification_type"],
                name="unique_notification_per_bitacora_event",
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.full_name}"
