from django.contrib import admin
from .models import BitacoraDocument, BitacoraEntry, Case, CaseAppointment, CaseAssignment

admin.site.register(Case)
admin.site.register(CaseAssignment)
admin.site.register(CaseAppointment)
admin.site.register(BitacoraEntry)
admin.site.register(BitacoraDocument)
