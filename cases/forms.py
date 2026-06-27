from pathlib import Path

from django import forms
from django.utils import timezone
from accounts.models import User
from .models import BitacoraEntry, Case

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget",
            MultipleFileInput(attrs={
                "class": "hidden-file-input",
                "multiple": True
            }),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """
        Convierte múltiples archivos en lista limpia
        """
        if not data:
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        cleaned = []
        for f in data:
            cleaned.append(super().clean(f, initial))

        return cleaned

class BitacoraEntryForm(forms.ModelForm):

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".png",
        ".jpg",
        ".jpeg",
        ".zip",
    }

    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "image/png",
        "image/jpeg",
        "application/zip",
        "application/x-zip-compressed",
        "multipart/x-zip",
        "application/octet-stream",
    }

    MAX_TOTAL_UPLOAD_SIZE = 7 * 1024 * 1024 * 1024  # 7GB

    files = MultipleFileField(
        required=False,
        help_text="PDF, Word, Excel, PowerPoint, PNG, JPG o ZIP. Tamaño total máximo: 7 GB.",
    )

    class Meta:
        model = BitacoraEntry
        fields = [
            "event_type",
            "content",
            "scheduled_for",
            "starts_new_term",
            "term_due_at",
            "notify",
        ]

        widgets = {
            "event_type": forms.Select(attrs={"class": "form-select"}),

            "content": forms.Textarea(attrs={
                "class": "form-textarea",
                "placeholder": "Describe el evento, actuación o novedad registrada en el caso...",
                "rows": 5,
            }),

            "scheduled_for": forms.DateTimeInput(
                attrs={
                    "class": "form-input",
                    "type": "datetime-local"
                },
                format="%Y-%m-%dT%H:%M"
            ),

            "term_due_at": forms.DateTimeInput(
                attrs={
                    "class": "form-input",
                    "type": "datetime-local"
                },
                format="%Y-%m-%dT%H:%M"
            ),

            "notify": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "starts_new_term": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }

        labels = {
            "event_type": "Tipo de evento",
            "content": "Descripción",
            "scheduled_for": "Fecha y hora del evento",
            "starts_new_term": "Empezar a contar nuevo término",
            "term_due_at": "Vencimiento del término",
            "notify": "Enviar también por correo",
        }

        error_messages = {
            "content": {
                "required": "Campos obligatorios incompletos: escribe la descripción del evento.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event_type"].required = False

    def clean_files(self):
        """
        Valida extensiones, tipos MIME conocidos y tamaño total de la carga.
        """
        files = self.cleaned_data.get("files", [])
        total_size = 0

        for file in files:
            extension = Path(file.name).suffix.lower()
            content_type = getattr(file, "content_type", None)

            if extension not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    "Formato no permitido. Adjunta PDF, Word, Excel, PowerPoint, PNG, JPG o ZIP."
                )

            if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
                raise forms.ValidationError(
                    "Tipo de archivo no permitido. Adjunta PDF, Word, Excel, PowerPoint, PNG, JPG o ZIP."
                )

            total_size += getattr(file, "size", 0) or 0

        if total_size > self.MAX_TOTAL_UPLOAD_SIZE:
            raise forms.ValidationError(
                "La carga total supera el máximo permitido de 7 GB."
            )

        return files

    def clean_content(self):
        content = (self.cleaned_data.get("content") or "").strip()
        if not content:
            raise forms.ValidationError("Campos obligatorios incompletos: escribe la descripción del evento.")
        return content

    def clean_event_type(self):
        return self.cleaned_data.get("event_type") or BitacoraEntry.EventType.SEGUIMIENTO

    def clean(self):
        cleaned_data = super().clean()
        now = timezone.now()

        starts_new_term = cleaned_data.get("starts_new_term")
        term_due_at = cleaned_data.get("term_due_at")
        scheduled_for = cleaned_data.get("scheduled_for")

        if starts_new_term and not term_due_at:
            self.add_error(
                "term_due_at",
                "Indica la fecha y hora en que vence el nuevo término.",
            )

        if scheduled_for:
            dt = scheduled_for
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            if dt < now:
                self.add_error("scheduled_for", "La fecha del evento no puede estar en el pasado.")

        if term_due_at:
            dt = term_due_at
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            if dt < now:
                self.add_error("term_due_at", "La fecha de vencimiento no puede estar en el pasado.")

        return cleaned_data


# ================================
# FORM REPARTO / ASIGNACIÓN
# ================================
class CaseDistributionForm(forms.Form):

    CATEGORY_TYPES = {
        "PEN": [
            ("PROC", "Proceso"),
            ("DER_PET", "Derecho de petición"),
            ("TUT", "Tutela"),
            ("CONC_DEN", "Concepto + denuncia"),
            ("CONC", "Concepto"),
            ("MEM", "Memorial"),
        ],
        "LAB": [
            ("PROC", "Proceso"),
            ("LIQ", "Liquidación"),
            ("LIQ_CONC", "Liquidación + concepto"),
            ("TUT", "Tutela"),
            ("DER_PET", "Derecho de petición"),
            ("CONC", "Concepto"),
            ("QUE", "Queja"),
            ("MEM", "Memorial"),
        ],
        "CIV": [
            ("PROC", "Proceso"),
            ("COB_PRE", "Cobro pre-jurídico"),
            ("TUT", "Tutela"),
            ("DER_PET", "Derecho de petición"),
            ("CONC_DP", "Concepto + DP"),
            ("QUE", "Queja"),
            ("MEM", "Memorial"),
            ("CONC", "Concepto"),
            ("CLI_EMP", "Clínica empresarial"),
        ],
        "FAM": [
            ("PROC", "Proceso"),
            ("CONC_DP", "Concepto + DP"),
            ("DER_PET", "Derecho de petición"),
            ("TUT", "Tutela"),
            ("MEM", "Memorial"),
            ("QUE", "Queja"),
            ("COB_PRE", "Cobro pre-jurídico"),
            ("CONC", "Concepto"),
        ],
        "DER_PUB_MIG": [
            ("SOL_REF", "Solicitud de refugio"),
            ("SOL_REF_DP", "Solicitud de refugio + DP"),
            ("SOL_REF_TUT", "Solicitud de refugio + Tutela"),
            ("TRAM_SAL", "Trámite salvoconducto"),
            ("TUT", "Tutela"),
            ("CONC_DP", "Concepto + DP"),
            ("DER_PET", "Derecho de petición"),
            ("CONC", "Concepto"),
        ],
        Case.CaseCategory.PUBLICO: list(Case.PublicoType.choices),
        Case.CaseCategory.PUBLICO_MIGRANTES: list(Case.PublicoMigrantesType.choices),
    }

    category = forms.ChoiceField(
        choices=[("", "Seleccione la sala")] + [
            ("PEN", "Sala Penal"),
            ("LAB", "Sala Laboral"),
            ("CIV", "Sala Civil"),
            ("FAM", "Sala Familia"),
            ("DER_PUB_MIG", "Sala Derecho Público"),
        ] + [c for c in Case.CaseCategory.choices if c[0] not in ("PEN", "LAB", "CIV", "FAM", "DER_PUB_MIG")],
        required=True,
        label="Sala",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    case_type = forms.ChoiceField(
        choices=[("", "Seleccione el trámite jurídico")],
        required=True,
        label="Trámite Jurídico",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_case_type"
        }),
    )

    assigned_student = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        label="Estudiante asignado",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    notes = forms.CharField(
        required=False,
        label="Notas",
        widget=forms.Textarea(attrs={
            "class": "form-textarea",
            "rows": 3,
        }),
    )

    def __init__(self, *args, **kwargs):
        self.case = kwargs.pop("case", None)
        super().__init__(*args, **kwargs)

        from django.db.models import Count, Q

        active_statuses = [
            Case.CaseStatus.ASIGNADO,
            Case.CaseStatus.AUTOASIGNADO,
            Case.CaseStatus.EN_PROCESO,
            Case.CaseStatus.ESPERANDO_BENEFICIARIO,
            Case.CaseStatus.EN_REVISION,
        ]
        students = (
            User.objects.filter(role=User.Role.ESTUDIANTE, is_active=True)
            .annotate(
                active_case_count=Count(
                    "assigned_cases",
                    filter=Q(assigned_cases__status__in=active_statuses),
                    distinct=True,
                )
            )
            .order_by("active_case_count", "first_name", "last_name")
        )
        self.fields["assigned_student"].queryset = students
        self.fields["assigned_student"].empty_label = "Seleccione el estudiante"
        self.fields["assigned_student"].label_from_instance = (
            lambda student: f"{student.full_name} - {student.active_case_count} casos activos"
        )

        if self.case and not self.is_bound:
            self.fields["category"].initial = self.case.category
            self.fields["case_type"].initial = self.case.case_type_specific

        category_id = self.data.get("category") if self.is_bound else getattr(self.case, "category", None)
        if category_id:
            self.fields["case_type"].choices = [
                ("", "Seleccione el trámite jurídico")
            ] + self.CATEGORY_TYPES.get(category_id, [])

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if not category:
            raise forms.ValidationError("Seleccione una sala.")
        return category

    def clean_case_type(self):
        case_type = self.cleaned_data.get("case_type")
        if not case_type:
            raise forms.ValidationError("Seleccione un trámite jurídico.")
        return case_type

    def clean_assigned_student(self):
        student = self.cleaned_data.get("assigned_student")

        if not student:
            raise forms.ValidationError("Debe seleccionar un estudiante.")

        if student.role != User.Role.ESTUDIANTE:
            raise forms.ValidationError("El usuario no es estudiante.")

        if not student.is_active:
            raise forms.ValidationError("El estudiante no está activo.")

        return student
