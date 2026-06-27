from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, document_number, password=None, **extra_fields):
        if not document_number:
            raise ValueError("El número de documento es obligatorio.")

        document_number = str(document_number).strip()

        user = self.model(document_number=document_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, document_number, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.SECRETARIA)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(document_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        BENEFICIARIO = "BEN", "Beneficiario/Usuario"
        SECRETARIA = "SEC", "Secretaría"
        ESTUDIANTE = "EST", "Estudiante"
        ASESOR = "ASE", "Asesor"

    class Gender(models.TextChoices):
        FEMENINO = "F", "Femenino"
        MASCULINO = "M", "Masculino"
        OTRO = "O", "Otro"
        NO_REPORTA = "N", "No reporta"

    document_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de documento",
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Nombres",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Apellidos",
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo electrónico",
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        null=True,
        blank=True,
        verbose_name="Sexo",
    )
    socioeconomic_stratum = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Estrato",
    )
    role = models.CharField(
        max_length=3,
        choices=Role.choices,
        verbose_name="Rol",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "document_number"
    REQUIRED_FIELDS = ["first_name"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["document_number"]

    def __str__(self):
        return f"{self.document_number} - {self.get_role_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self):
        name = self.full_name.strip()
        if not name:
            return "U"

        parts = name.split()
        if len(parts) == 1:
            return parts[0][0].upper()

        return (parts[0][0] + parts[-1][0]).upper()
