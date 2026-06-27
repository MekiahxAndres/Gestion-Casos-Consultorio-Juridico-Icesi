from django.urls import path

from .views import (
    AdvisorAvailabilityCreateAPIView,
    AdvisorAvailabilityDeleteAPIView,
    AssignedCaseDetailView,
    AssignedCasesAPIView,
    AssignedCasesCategoriesView,
    AssignedCasesFilteredView,
    CaseBitacoraView,
    CaseCalendarEventCreateAPIView,
    CaseCalendarEventDeleteAPIView,
    CaseCalendarEventsAPIView,
    ClosedCasesAPIView,
    CaseClosureAPIView,
    CaseDetailView,
    CaseDistributionListView,
    CaseDistributionView,
    CaseAppointmentDetailView,
    CaseReportView,
    CaseSearchAPIView,
    CaseSearchByIdAPIView,
    CaseSearchUnassignedByIdAPIView,
    CaseStatusChangeAPIView,
    DelayedCasesDashboardView,
    MissedAppointmentsDashboardView,
    PendingCasesView,
    ReassignCaseView,
    SecretaryCasesView,
    SendMeetingInvitationAPIView,
    calendario_seguimientos,
    ejecutar_reparto,
    panel_secretaria,
)
from cases import views

urlpatterns = [
    # Gestión principal de casos
    path("secretaria/casos/", SecretaryCasesView.as_view(), name="secretary_cases"),
    path("reporte/", CaseReportView.as_view(), name="case_report"),

    # Reparto / distribución
    path("casos/distribuir/", CaseDistributionListView.as_view(), name="case_distribution_list"),
    path("casos/<int:case_id>/distribucion/", CaseDistributionView.as_view(), name="case_distribution"),
    path("panel/", panel_secretaria, name="panel_secretaria"),
    path("repartir/<int:caso_id>/", ejecutar_reparto, name="ejecutar_reparto"),

    # Consulta y detalle
    path("casos/retrasados/", DelayedCasesDashboardView.as_view(), name="delayed_cases_dashboard"),
    path("citas/no-atendidas/", MissedAppointmentsDashboardView.as_view(), name="missed_appointments_dashboard"),
    path("citas/<int:appointment_id>/", CaseAppointmentDetailView.as_view(), name="case_appointment_detail"),
    path("casos/<int:case_id>/", CaseDetailView.as_view(), name="case_detail"),
    path("casos/<int:case_id>/reasignar/", ReassignCaseView.as_view(), name="reassign_case"),
    path("casos/<int:case_id>/bitacora/", CaseBitacoraView.as_view(), name="case_bitacora"),

    # Casos asignados / filtros / salas
    path("casos/asignados/categorias/", AssignedCasesCategoriesView.as_view(), name="assigned_cases_categories"),
    path("casos/asignados/filtrados/", AssignedCasesFilteredView.as_view(), name="assigned_cases_filtered"),
    path("api/casos/asignados/", AssignedCasesAPIView.as_view(), name="assigned_cases_api"),
    path("api/casos/buscar/", CaseSearchAPIView.as_view(), name="case_search_api"),
    path("api/casos/buscar-por-id/", CaseSearchByIdAPIView.as_view(), name="case_search_by_id_api"),
    path("api/casos/buscar-sin-asignar/", CaseSearchUnassignedByIdAPIView.as_view(), name="case_search_unassigned_api"),
    path("api/casos/cambiar-estado/", CaseStatusChangeAPIView.as_view(), name="case_status_change_api"),
    path("api/casos/cerrar/", CaseClosureAPIView.as_view(), name="case_closure_api"),
    path("api/casos/cerrados/", ClosedCasesAPIView.as_view(), name="closed_cases_api"),

    # HU1 / HU2
    path("pending/", PendingCasesView.as_view(), name="pending_cases"),
    path("assigned/<int:case_id>/", AssignedCaseDetailView.as_view(), name="assigned_case_detail"),

    # Calendario por caso
    path("casos/<int:case_id>/calendario/eventos/", CaseCalendarEventsAPIView.as_view(), name="case_calendar_events"),
    path("casos/<int:case_id>/calendario/evento/crear/", CaseCalendarEventCreateAPIView.as_view(), name="case_calendar_event_create"),
    path("casos/<int:case_id>/calendario/evento/<int:event_id>/eliminar/", CaseCalendarEventDeleteAPIView.as_view(), name="case_calendar_event_delete"),
    path("casos/<int:case_id>/calendario/disponibilidad/crear/", AdvisorAvailabilityCreateAPIView.as_view(), name="case_availability_create"),
    path("casos/<int:case_id>/calendario/disponibilidad/<int:slot_id>/eliminar/", AdvisorAvailabilityDeleteAPIView.as_view(), name="case_availability_delete"),
    path("casos/<int:case_id>/calendario/disponibilidad/<int:slot_id>/solicitar/", SendMeetingInvitationAPIView.as_view(), name="case_meeting_invitation"),

    # Otros
    path("calendario/", calendario_seguimientos, name="calendario_seguimientos"),

    path('distribuir/automatico/', views.reparto_automatico_view, name='reparto_automatico'),

    path("ajax/load-case-types/", views.load_case_types, name="ajax_load_case_types"),

]
