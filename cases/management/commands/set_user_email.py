from django.core.management.base import BaseCommand
from accounts.models import User


REAL_EMAILS = {
    # Agrega aquí: 'numero_documento': 'correo@dominio.com'
}


class Command(BaseCommand):
    help = "Actualiza el correo de un usuario por su número de documento."

    def add_arguments(self, parser):
        parser.add_argument("--doc", help="Número de documento del usuario")
        parser.add_argument("--email", help="Correo electrónico a asignar")
        parser.add_argument("--list", action="store_true", help="Listar todos los usuarios y sus correos actuales")

    def handle(self, *args, **options):
        if options["list"]:
            self._list_users()
            return

        doc = options.get("doc")
        email = options.get("email")

        if not doc or not email:
            self.stdout.write(self.style.ERROR("Usa --doc <numero> --email <correo>  o  --list"))
            return

        self._set_email(doc, email)

    def _list_users(self):
        users = User.objects.all().order_by("role", "document_number")
        self.stdout.write("\n{:<10} {:<12} {:<30} {:<35}".format("Rol", "Documento", "Nombre", "Correo actual"))
        self.stdout.write("-" * 90)
        for u in users:
            self.stdout.write("{:<10} {:<12} {:<30} {:<35}".format(
                u.get_role_display(),
                u.document_number,
                u.full_name[:28],
                u.email or "(sin correo)",
            ))

    def _set_email(self, doc, email):
        try:
            user = User.objects.get(document_number=doc)
            old_email = user.email or "(vacío)"
            user.email = email
            user.save(update_fields=["email"])
            self.stdout.write(self.style.SUCCESS(
                f"OK: {user.full_name} ({doc}): {old_email} -> {email}"
            ))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No se encontró usuario con documento: {doc}"))
