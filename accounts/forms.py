from django import forms
from cases.models import BitacoraEntry


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        return data


class BitacoraEntryForm(forms.ModelForm):
    files = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'hidden-file-input',
            'id': 'id_files',
            'multiple': True,
        })
    )

    class Meta:
        model = BitacoraEntry
        fields = ['entry_type', 'content', 'scheduled_for', 'notify']
        widgets = {
            'entry_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Escribe aquí tus observaciones, actualizaciones del caso, notas de entrevistas, etc...'
            }),
            'scheduled_for': forms.DateTimeInput(
                attrs={'class': 'form-input', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'notify': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entry_type'].label = 'Tipo de entrada'
        self.fields['content'].label = 'Nota o actualización'
        self.fields['scheduled_for'].label = 'Fecha del evento'
        self.fields['notify'].label = 'Marcar como notificado'
        self.fields['files'].label = 'Adjuntar archivos'
        self.fields['scheduled_for'].required = False
