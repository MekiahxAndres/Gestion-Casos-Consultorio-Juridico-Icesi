from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User


class Command(BaseCommand):
    help = "Prueba el envío de correo SMTP y muestra el estado de los emails de usuarios."

    def add_arguments(self, parser):
        parser.add_argument("--to", help="Dirección de destino para prueba SMTP")
        parser.add_argument("--usuarios", action="store_true", help="Muestra usuarios y sus correos actuales")

    def handle(self, *args, **options):
        self.stdout.write("\n=== Configuración de correo ===")
        self.stdout.write(f"  BACKEND : {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  HOST    : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"  TLS     : {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"  USER    : {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"  FROM    : {settings.DEFAULT_FROM_EMAIL}")
        pwd = settings.EMAIL_HOST_PASSWORD
        self.stdout.write(f"  PASSWORD: {'OK configurada (' + str(len(pwd)) + ' chars)' if pwd else 'VACIA - falta configurar'}")

        if options["usuarios"]:
            self._list_users()

        if options["to"]:
            self._send_test(options["to"])
        elif not options["usuarios"]:
            self.stdout.write(self.style.WARNING(
                "\nUsa --to correo@ejemplo.com para enviar correo de prueba"
                "\nUsa --usuarios para ver los correos de todos los usuarios"
            ))

    def _list_users(self):
        self.stdout.write("\n=== Usuarios en la base de datos ===")
        users = User.objects.all().order_by("role", "document_number")
        self.stdout.write("{:<12} {:<12} {:<28} {:<35}".format("Rol", "Documento", "Nombre", "Correo"))
        self.stdout.write("-" * 90)
        for u in users:
            email_display = u.email if u.email else self.style.ERROR("(sin correo)")
            self.stdout.write("{:<12} {:<12} {:<28} {}".format(
                u.get_role_display(),
                u.document_number,
                u.full_name[:26],
                email_display,
            ))

    def _send_test(self, to_email):
        self.stdout.write(f"\n=== Enviando correo de prueba a {to_email} ===")
        try:
            send_mail(
                subject="Prueba SMTP — Consultorio Jurídico",
                message="Este es un correo de prueba del sistema del Consultorio Jurídico ICESI.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message="""
                <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;">
                  <div style="background:#5454e8;padding:20px 28px;border-radius:8px 8px 0 0;">
                    <h1 style="color:white;margin:0;font-size:18px;">Consultorio Jurídico ICESI</h1>
                  </div>
                  <div style="background:white;border:1px solid #e5e7eb;padding:24px 28px;border-radius:0 0 8px 8px;">
                    <p style="color:#374151;">✅ El sistema de correo está funcionando correctamente.</p>
                    <p style="color:#6b7280;font-size:13px;">Este es un mensaje de prueba generado por el comando de gestión.</p>
                  </div>
                </div>""",
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"OK - Correo enviado correctamente a {to_email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERROR al enviar: {e}"))
            self.stdout.write(self.style.WARNING(
                "\nPosibles causas:\n"
                "  - La contraseña de aplicación de Gmail es incorrecta\n"
                "  - La cuenta no tiene activada la verificación en 2 pasos\n"
                "  - No se generó una 'App Password' para esta app\n"
                "  - El archivo .env no se está cargando correctamente"
            ))
