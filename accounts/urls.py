from django.urls import path

from .views import (
    AdvisorDashboardView,
    BeneficiaryAppointmentsView,
    BeneficiaryDashboardView,
    DashboardRedirectView,
    LogoutView,
    NotificationsCenterView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RoleLoginView,
    RoleSelectionView,
    SecretaryDashboardView,
    SplashView,
    StudentDashboardView,
)

urlpatterns = [
    # Inicio
    path("", SplashView.as_view(), name="splash"),

    # Autenticación
    path("seleccion-rol/", RoleSelectionView.as_view(), name="role_selection"),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("login/<str:role>/", RoleLoginView.as_view(), name="role_login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Redirección por rol
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard_redirect"),

    # Dashboards
    path(
        "beneficiario/dashboard/",
        BeneficiaryDashboardView.as_view(),
        name="beneficiary_dashboard",
    ),
    path(
        "beneficiario/citas/",
        BeneficiaryAppointmentsView.as_view(),
        name="beneficiary_appointments",
    ),
    path(
        "secretaria/dashboard/",
        SecretaryDashboardView.as_view(),
        name="secretary_dashboard",
    ),
    path(
        "estudiante/dashboard/",
        StudentDashboardView.as_view(),
        name="student_dashboard",
    ),
    path(
        "asesor/dashboard/",
        AdvisorDashboardView.as_view(),
        name="advisor_dashboard",
    ),

    # Notificaciones
    path(
        "notificaciones/",
        NotificationsCenterView.as_view(),
        name="notifications_center",
    ),

    # Recuperación de contraseña
    path("recuperar-contrasena/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("recuperar-contrasena/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("recuperar-contrasena/completado/", PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
