import os
import json
import shutil
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.services import notify_advisor_document_uploaded, notify_advisor_important_event
from accounts.models import User
from .forms import BitacoraEntryForm
from .models import (
    AdvisorAvailabilitySlot,
    BitacoraDocument,
    BitacoraEntry,
    Case,
    CaseAppointment,
    CaseCalendarEvent,
    CaseDeadline,
    Notification,
)


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class CasesFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.secretaria = User.objects.create_user(
            document_number="1000000001",
            password="123456",
            first_name="Ana María",
            last_name="López",
            role=User.Role.SECRETARIA,
            email="secretaria@email.com",
            is_active=True,
        )

        self.estudiante_actual = User.objects.create_user(
            document_number="1000000002",
            password="123456",
            first_name="Carlos",
            last_name="Ramírez",
            role=User.Role.ESTUDIANTE,
            email="estudiante@email.com",
            is_active=True,
        )

        self.estudiante_nuevo = User.objects.create_user(
            document_number="1000000004",
            password="123456",
            first_name="Laura",
            last_name="Torres",
            role=User.Role.ESTUDIANTE,
            email="laura@email.com",
            is_active=True,
        )

        self.asesor = User.objects.create_user(
            document_number="1000000003",
            password="123456",
            first_name="Roberto",
            last_name="Gómez",
            role=User.Role.ASESOR,
            email="asesor@email.com",
            is_active=True,
        )

        self.beneficiario = User.objects.create_user(
            document_number="1234567890",
            password="1234567890",
            first_name="María",
            last_name="González Pérez",
            role=User.Role.BENEFICIARIO,
            email="maria@email.com",
            is_active=True,
        )

        self.case = Case.objects.create(
            case_number="12345",
            title="Caso de familia - custodia y visitas",
            description="Solicitud de regulación de visitas y cuota alimentaria para menor de edad.",
            category=Case.CaseCategory.FAMILIA,
            status=Case.CaseStatus.ASIGNADO,
            beneficiary=self.beneficiario,
            assigned_student=self.estudiante_actual,
            advisor=self.asesor,
            secretary=self.secretaria,
        )

    def tearDown(self):
        for document in BitacoraDocument.objects.all():
            if document.file and hasattr(document.file, "path") and os.path.isfile(document.file.path):
                os.remove(document.file.path)

    def test_secretaria_puede_reasignar_caso(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse("reassign_case", args=[self.case.id]),
            {
                "new_student": self.estudiante_nuevo.id,
                "reason": "Balanceo de carga entre estudiantes",
            },
            follow=True,
        )

        self.case.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.case.assigned_student, self.estudiante_nuevo)

        bitacora = BitacoraEntry.objects.filter(case=self.case).order_by("-created_at").first()
        self.assertIsNotNone(bitacora)
        self.assertEqual(bitacora.author, self.secretaria)
        self.assertEqual(bitacora.entry_type, BitacoraEntry.EntryType.ASIGNACION)
        self.assertIn("Balanceo de carga", bitacora.content)

    def test_secretaria_no_puede_reasignar_al_mismo_estudiante(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse("reassign_case", args=[self.case.id]),
            {
                "new_student": self.estudiante_actual.id,
                "reason": "Intento inválido",
            },
            follow=True,
        )

        self.case.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.case.assigned_student, self.estudiante_actual)
        self.assertContains(
            response,
            "El caso ya está asignado a este estudiante."
        )
        self.assertEqual(BitacoraEntry.objects.filter(case=self.case).count(), 0)

    def test_estudiante_no_puede_reasignar_caso(self):
        self.client.force_login(self.estudiante_actual)

        response = self.client.post(
            reverse("reassign_case", args=[self.case.id]),
            {
                "new_student": self.estudiante_nuevo.id,
                "reason": "Intento no autorizado",
            },
            follow=True,
        )

        self.case.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.case.assigned_student, self.estudiante_actual)
        self.assertEqual(BitacoraEntry.objects.filter(case=self.case).count(), 0)

    def test_no_se_reasigna_si_estudiante_no_existe(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse("reassign_case", args=[self.case.id]),
            {
                "new_student": 999999,
                "reason": "Prueba estudiante inválido",
            },
            follow=True,
        )

        self.case.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.case.assigned_student, self.estudiante_actual)
        self.assertContains(response, "El estudiante seleccionado no es válido.")

    def test_si_caso_estaba_sin_asignar_pasa_a_asignado(self):
        self.case.assigned_student = None
        self.case.status = Case.CaseStatus.SIN_ASIGNAR
        self.case.save()

        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse("reassign_case", args=[self.case.id]),
            {
                "new_student": self.estudiante_nuevo.id,
                "reason": "Asignación inicial",
            },
            follow=True,
        )

        self.case.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.case.assigned_student, self.estudiante_nuevo)
        self.assertEqual(self.case.status, Case.CaseStatus.ASIGNADO)

    def test_estudiante_puede_subir_documento_valido_y_guardar_metadata(self):
        self.client.force_login(self.estudiante_actual)

        archivo = SimpleUploadedFile(
            "evidencia.pdf",
            b"%PDF-1.4 archivo de prueba",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Se adjunta evidencia del caso.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        entry = BitacoraEntry.objects.filter(
            case=self.case,
            author=self.estudiante_actual
        ).order_by("-created_at").first()

        self.assertIsNotNone(entry)
        self.assertEqual(entry.entry_type, BitacoraEntry.EntryType.DOCUMENTO)

        documento = BitacoraDocument.objects.filter(entry=entry).first()
        self.assertIsNotNone(documento)
        self.assertEqual(documento.original_name, "evidencia.pdf")
        self.assertTrue(bool(documento.file))
        self.assertEqual(documento.file_size, len(b"%PDF-1.4 archivo de prueba"))
        self.assertEqual(documento.content_type, "application/pdf")
        self.assertIsNotNone(documento.uploaded_at)

    def test_subida_documento_notifica_al_asesor_asignado(self):
        self.client.force_login(self.estudiante_actual)

        archivo = SimpleUploadedFile(
            "entregable.pdf",
            b"%PDF-1.4 soporte",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Se adjunta entregable para revisión.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        documento = BitacoraDocument.objects.get(original_name="entregable.pdf")
        notification = Notification.objects.get(
            recipient=self.asesor,
            case=self.case,
            related_document=documento,
            notification_type=Notification.NotificationType.DOCUMENT_UPLOAD,
        )
        self.assertIn(self.case.case_number, notification.message)
        self.assertIn("entregable.pdf", notification.message)

    def test_notificacion_documento_no_se_duplica(self):
        self.client.force_login(self.estudiante_actual)

        archivo = SimpleUploadedFile(
            "unico.pdf",
            b"%PDF-1.4 unico",
            content_type="application/pdf"
        )

        self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Documento único.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        documento = BitacoraDocument.objects.get(original_name="unico.pdf")
        notify_advisor_document_uploaded(documento)

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.asesor,
                related_document=documento,
                notification_type=Notification.NotificationType.DOCUMENT_UPLOAD,
            ).count(),
            1,
        )

    def test_si_no_hay_asesor_no_envia_alerta_y_registra_evento(self):
        self.case.advisor = None
        self.case.save(update_fields=["advisor"])
        self.client.force_login(self.estudiante_actual)

        archivo = SimpleUploadedFile(
            "sin-asesor.pdf",
            b"%PDF-1.4 sin asesor",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Soporte sin asesor asignado.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Notification.objects.filter(
                notification_type=Notification.NotificationType.DOCUMENT_UPLOAD,
            ).count(),
            0,
        )
        self.assertTrue(
            BitacoraEntry.objects.filter(
                case=self.case,
                entry_type=BitacoraEntry.EntryType.EVENTO,
                content__startswith="Alerta no enviada",
            ).exists()
        )

    def test_estudiante_asignado_registra_evento_y_notifica_participantes(self):
        self.client.force_login(self.estudiante_actual)

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.EVENTO,
                "content": "Audiencia programada con el beneficiario.",
                "notify": False,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        entry = BitacoraEntry.objects.get(
            case=self.case,
            author=self.estudiante_actual,
            entry_type=BitacoraEntry.EntryType.EVENTO,
            content="Audiencia programada con el beneficiario.",
        )
        notification = Notification.objects.get(
            recipient=self.asesor,
            case=self.case,
            related_entry=entry,
            notification_type=Notification.NotificationType.INFO,
        )
        self.assertIn(self.case.case_number, notification.message)
        self.assertIn("Audiencia programada", notification.message)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.secretaria,
                case=self.case,
                related_entry=entry,
                notification_type=Notification.NotificationType.INFO,
            ).exists()
        )

        bitacora_response = self.client.get(reverse("case_bitacora", args=[self.case.id]))
        self.assertContains(bitacora_response, "Seguimiento del caso")

        self.client.force_login(self.asesor)
        notifications_response = self.client.get(reverse("notifications_center"))
        self.assertContains(notifications_response, "Eventos importantes")
        self.assertContains(notifications_response, "Audiencia programada")

    def test_bitacora_anonimo_redirige_al_login(self):
        response = self.client.get(reverse("case_bitacora", args=[self.case.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/login/"))

    def test_bitacora_muestra_resumen_asistido(self):
        self.client.force_login(self.secretaria)

        response = self.client.get(reverse("case_bitacora", args=[self.case.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumen asistido del caso")
        self.assertContains(response, "Registrar evento del caso")

    def test_evento_importante_sin_descripcion_no_se_guarda(self):
        self.client.force_login(self.estudiante_actual)

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.EVENTO,
                "content": "   ",
                "notify": False,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campos obligatorios incompletos")
        self.assertFalse(
            BitacoraEntry.objects.filter(
                case=self.case,
                author=self.estudiante_actual,
                entry_type=BitacoraEntry.EntryType.EVENTO,
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                notification_type=Notification.NotificationType.IMPORTANT_EVENT,
            ).exists()
        )

    def test_notificacion_evento_importante_no_se_duplica(self):
        entry = BitacoraEntry.objects.create(
            case=self.case,
            author=self.estudiante_actual,
            entry_type=BitacoraEntry.EntryType.EVENTO,
            content="Evento con una sola alerta.",
        )

        notify_advisor_important_event(entry)
        notify_advisor_important_event(entry)

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.asesor,
                related_entry=entry,
                notification_type=Notification.NotificationType.IMPORTANT_EVENT,
            ).count(),
            1,
        )

    def test_evento_sin_asesor_notifica_a_secretaria(self):
        self.case.advisor = None
        self.case.save(update_fields=["advisor"])
        self.client.force_login(self.estudiante_actual)

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.EVENTO,
                "content": "Evento sin asesor asignado.",
                "notify": False,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        notification = Notification.objects.get(
            recipient=self.secretaria,
            case=self.case,
            notification_type=Notification.NotificationType.INFO,
        )
        self.assertIn("Evento sin asesor", notification.message)

    def test_secretaria_tambien_puede_subir_documento(self):
        self.client.force_login(self.secretaria)

        archivo = SimpleUploadedFile(
            "memo.pdf",
            b"%PDF-1.4 memo",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.ACTUALIZACION,
                "content": "Secretaría adjunta soporte administrativo.",
                "notify": True,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        entry = BitacoraEntry.objects.filter(
            case=self.case,
            author=self.secretaria
        ).order_by("-created_at").first()

        self.assertIsNotNone(entry)
        documento = BitacoraDocument.objects.filter(entry=entry).first()
        self.assertIsNotNone(documento)
        self.assertEqual(documento.original_name, "memo.pdf")

    def test_beneficiario_no_puede_subir_documento(self):
        self.client.force_login(self.beneficiario)

        archivo = SimpleUploadedFile(
            "archivo.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Intento no autorizado.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BitacoraDocument.objects.count(), 0)

    def test_estudiante_no_asignado_no_puede_subir_documento(self):
        otro_estudiante = User.objects.create_user(
            document_number="1000000005",
            password="123456",
            first_name="Mateo",
            last_name="Ruiz",
            role=User.Role.ESTUDIANTE,
            email="mateo@email.com",
            is_active=True,
        )

        self.client.force_login(otro_estudiante)

        archivo = SimpleUploadedFile(
            "archivo.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Intento no autorizado del estudiante no asignado.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BitacoraDocument.objects.count(), 0)

    def test_se_guardan_dos_documentos_en_una_misma_entrada(self):
        self.client.force_login(self.estudiante_actual)

        archivo1 = SimpleUploadedFile(
            "doc1.pdf",
            b"%PDF-1.4 uno",
            content_type="application/pdf"
        )
        archivo2 = SimpleUploadedFile(
            "doc2.pdf",
            b"%PDF-1.4 dos",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Se adjuntan dos soportes.",
                "notify": False,
                "files": [archivo1, archivo2],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        entry = BitacoraEntry.objects.filter(
            case=self.case,
            author=self.estudiante_actual
        ).order_by("-created_at").first()

        self.assertIsNotNone(entry)

        documentos = BitacoraDocument.objects.filter(entry=entry).order_by("original_name")
        self.assertEqual(documentos.count(), 2)
        self.assertEqual(documentos[0].original_name, "doc1.pdf")
        self.assertEqual(documentos[1].original_name, "doc2.pdf")

    def test_rechaza_formato_no_permitido(self):
        self.client.force_login(self.estudiante_actual)

        archivo = SimpleUploadedFile(
            "malicioso.exe",
            b"MZ fake exe",
            content_type="application/x-msdownload"
        )

        response = self.client.post(
            reverse("case_bitacora", args=[self.case.id]),
            data={
                "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                "content": "Intento subir exe.",
                "notify": False,
                "files": [archivo],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formato no permitido")
        self.assertEqual(BitacoraDocument.objects.count(), 0)

    def test_rechaza_archivo_muy_pesado(self):
        self.client.force_login(self.estudiante_actual)

        contenido = b"a" * 9
        archivo = SimpleUploadedFile(
            "grande.pdf",
            contenido,
            content_type="application/pdf"
        )

        with patch.object(BitacoraEntryForm, "MAX_TOTAL_UPLOAD_SIZE", 8):
            response = self.client.post(
                reverse("case_bitacora", args=[self.case.id]),
                data={
                    "entry_type": BitacoraEntry.EntryType.DOCUMENTO,
                    "content": "Intento subir archivo grande.",
                    "notify": False,
                    "files": [archivo],
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "supera el máximo permitido")
        self.assertEqual(BitacoraDocument.objects.count(), 0)


class DelayedCasesDashboardTests(TestCase):
    def setUp(self):
        self.secretary = User.objects.create_user(
            document_number="SEC-DASH",
            password="123456",
            first_name="Sara",
            last_name="Secretaria",
            role=User.Role.SECRETARIA,
            is_active=True,
        )
        self.advisor = User.objects.create_user(
            document_number="ASE001",
            password="123456",
            first_name="Adriana",
            last_name="Asesora",
            role=User.Role.ASESOR,
            is_active=True,
        )
        self.other_advisor = User.objects.create_user(
            document_number="ASE002",
            password="123456",
            first_name="Otro",
            last_name="Asesor",
            role=User.Role.ASESOR,
            is_active=True,
        )
        self.student = User.objects.create_user(
            document_number="EST-DASH",
            password="123456",
            first_name="Esteban",
            last_name="Diaz",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )
        self.other_student = User.objects.create_user(
            document_number="EST-DASH-2",
            password="123456",
            first_name="Lina",
            last_name="Mora",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )
        self.beneficiary = User.objects.create_user(
            document_number="BEN-DASH",
            password="123456",
            first_name="Beatriz",
            last_name="Rojas",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        self.delayed_case = Case.objects.create(
            case_number="DL-001",
            title="Caso vencido",
            description="Caso con fecha limite vencida.",
            beneficiary=self.beneficiary,
            assigned_student=self.student,
            advisor=self.advisor,
            status=Case.CaseStatus.EN_PROCESO,
        )
        CaseDeadline.objects.create(
            case=self.delayed_case,
            created_by=self.advisor,
            title="Presentar memorial",
            description="Entrega pendiente.",
            due_date=timezone.now() - timedelta(days=2),
        )

        self.on_time_case = Case.objects.create(
            case_number="DL-002",
            title="Caso a tiempo",
            description="Caso con proxima fecha vigente.",
            beneficiary=self.beneficiary,
            assigned_student=self.student,
            advisor=self.advisor,
            status=Case.CaseStatus.ASIGNADO,
        )
        CaseDeadline.objects.create(
            case=self.on_time_case,
            created_by=self.advisor,
            title="Revision de documentos",
            description="Seguimiento programado.",
            due_date=timezone.now() + timedelta(days=5),
        )

        self.other_case = Case.objects.create(
            case_number="DL-003",
            title="Caso de otro asesor",
            description="No debe aparecer en este tablero.",
            beneficiary=self.beneficiary,
            assigned_student=self.other_student,
            advisor=self.other_advisor,
            status=Case.CaseStatus.EN_PROCESO,
        )
        CaseDeadline.objects.create(
            case=self.other_case,
            created_by=self.other_advisor,
            title="Vencimiento externo",
            description="Fuera del alcance del asesor autenticado.",
            due_date=timezone.now() - timedelta(days=1),
        )

    def test_asesor_visualiza_tablero_con_casos_clasificados(self):
        self.client.force_login(self.advisor)

        response = self.client.get(reverse("delayed_cases_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tablero de casos retrasados")
        self.assertContains(response, "Retrasados")
        self.assertContains(response, "A tiempo")
        self.assertContains(response, "DL-001")
        self.assertContains(response, "DL-002")
        self.assertContains(response, "Presentar memorial")
        self.assertNotContains(response, "DL-003")

    def test_secretaria_visualiza_tablero_con_todos_los_casos_activos(self):
        self.client.force_login(self.secretary)

        response = self.client.get(reverse("delayed_cases_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tablero de casos retrasados")
        self.assertContains(response, "DL-001")
        self.assertContains(response, "DL-002")
        self.assertContains(response, "DL-003")

    def test_panel_asesor_conserva_acceso_y_muestra_alertas_reales(self):
        self.client.force_login(self.advisor)

        response = self.client.get(reverse("advisor_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel de Supervisión - Asesor")
        self.assertContains(response, "Casos Retrasados")
        self.assertContains(response, "DL-001")
        self.assertContains(response, "Presentar memorial")
        self.assertContains(response, reverse("delayed_cases_dashboard"))

    def test_estudiante_visualiza_solo_sus_casos_asignados(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("delayed_cases_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tablero de casos retrasados")
        self.assertContains(response, "DL-001")
        self.assertContains(response, "DL-002")
        self.assertNotContains(response, "DL-003")

    def test_panel_estudiante_muestra_accesos_a_tableros(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Casos Retrasados")
        self.assertContains(response, "Citas No Atendidas")
        self.assertContains(response, reverse("delayed_cases_dashboard"))
        self.assertContains(response, reverse("missed_appointments_dashboard"))

    def test_beneficiario_no_puede_acceder_al_tablero(self):
        self.client.force_login(self.beneficiary)

        response = self.client.get(reverse("delayed_cases_dashboard"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No autorizado.")
        self.assertNotContains(response, "Tablero de casos retrasados")


class MissedAppointmentsDashboardTests(TestCase):
    def setUp(self):
        self.secretary = User.objects.create_user(
            document_number="SEC-HU1",
            password="123456",
            first_name="Sofia",
            last_name="Secretaria",
            role=User.Role.SECRETARIA,
            is_active=True,
        )
        self.advisor = User.objects.create_user(
            document_number="ASE-HU1",
            password="123456",
            first_name="Andres",
            last_name="Asesor",
            role=User.Role.ASESOR,
            is_active=True,
        )
        self.other_advisor = User.objects.create_user(
            document_number="ASE-HU1-2",
            password="123456",
            first_name="Clara",
            last_name="Asesora",
            role=User.Role.ASESOR,
            is_active=True,
        )
        self.student = User.objects.create_user(
            document_number="EST-HU1",
            password="123456",
            first_name="Estudiante",
            last_name="HU1",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )
        self.other_student = User.objects.create_user(
            document_number="EST-HU1-2",
            password="123456",
            first_name="Otro",
            last_name="Estudiante",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )
        self.beneficiary = User.objects.create_user(
            document_number="BEN-HU1",
            password="123456",
            first_name="Beneficiario",
            last_name="HU1",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        self.case = Case.objects.create(
            case_number="APT-001",
            title="Caso con cita vencida",
            description="Caso para validar citas no atendidas.",
            beneficiary=self.beneficiary,
            assigned_student=self.student,
            advisor=self.advisor,
            secretary=self.secretary,
            status=Case.CaseStatus.EN_PROCESO,
        )
        self.other_case = Case.objects.create(
            case_number="APT-002",
            title="Caso de otro asesor",
            description="Caso que no debe ver el asesor autenticado.",
            beneficiary=self.beneficiary,
            assigned_student=self.other_student,
            advisor=self.other_advisor,
            secretary=self.secretary,
            status=Case.CaseStatus.EN_PROCESO,
        )

        self.no_show_appointment = CaseAppointment.objects.create(
            case=self.case,
            title="Entrevista inicial",
            scheduled_for=timezone.now() - timedelta(days=2),
            status=CaseAppointment.AppointmentStatus.NO_SHOW,
            notes="El beneficiario no asistio.",
            created_by=self.secretary,
        )
        self.overdue_pending_appointment = CaseAppointment.objects.create(
            case=self.case,
            title="Seguimiento documental",
            scheduled_for=timezone.now() - timedelta(days=1),
            status=CaseAppointment.AppointmentStatus.PENDING,
            created_by=self.secretary,
        )
        self.attended_appointment = CaseAppointment.objects.create(
            case=self.case,
            title="Cita atendida",
            scheduled_for=timezone.now() - timedelta(days=3),
            status=CaseAppointment.AppointmentStatus.ATTENDED,
            created_by=self.secretary,
        )
        self.other_advisor_appointment = CaseAppointment.objects.create(
            case=self.other_case,
            title="Cita externa",
            scheduled_for=timezone.now() - timedelta(days=4),
            status=CaseAppointment.AppointmentStatus.NO_SHOW,
            created_by=self.secretary,
        )

    def test_secretaria_visualiza_todas_las_citas_no_atendidas(self):
        self.client.force_login(self.secretary)

        response = self.client.get(reverse("missed_appointments_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tablero de citas no atendidas")
        self.assertContains(response, "Entrevista inicial")
        self.assertContains(response, "Seguimiento documental")
        self.assertContains(response, "Cita externa")
        self.assertNotContains(response, "Cita atendida")

    def test_asesor_visualiza_solo_sus_citas_no_atendidas(self):
        self.client.force_login(self.advisor)

        response = self.client.get(reverse("missed_appointments_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entrevista inicial")
        self.assertContains(response, "Seguimiento documental")
        self.assertNotContains(response, "Cita externa")
        self.assertNotContains(response, "Cita atendida")

    def test_estudiante_visualiza_solo_citas_de_sus_casos_asignados(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("missed_appointments_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tablero de citas no atendidas")
        self.assertContains(response, "Entrevista inicial")
        self.assertContains(response, "Seguimiento documental")
        self.assertNotContains(response, "Cita externa")
        self.assertNotContains(response, "Cita atendida")

    def test_estudiante_no_puede_abrir_detalle_de_cita_ajena(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("case_appointment_detail", args=[self.other_advisor_appointment.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_beneficiario_no_puede_acceder(self):
        self.client.force_login(self.beneficiary)
        response = self.client.get(reverse("missed_appointments_dashboard"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No autorizado.")
        self.assertNotContains(response, "Tablero de citas no atendidas")

    def test_permite_abrir_detalle_de_cita_y_caso_asociado(self):
        self.client.force_login(self.advisor)

        dashboard_response = self.client.get(reverse("missed_appointments_dashboard"))
        detail_url = reverse("case_appointment_detail", args=[self.no_show_appointment.id])
        case_url = reverse("case_detail", args=[self.case.id])

        self.assertContains(dashboard_response, detail_url)
        self.assertContains(dashboard_response, case_url)

        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Detalle de cita")
        self.assertContains(detail_response, "Entrevista inicial")


# =========================
# HU3 - REPARTO DE CASOS
# =========================

class CaseDistributionTests(TestCase):
    """Pruebas para la funcionalidad de Reparto de Casos (HU3)."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Configura datos para las pruebas de reparto."""
        from cases.models import CaseDocument
        from cases.services import CaseCompletionValidator

        self.secretary = User.objects.create_user(
            document_number='SEC001',
            first_name='Secretaria',
            last_name='Reparto',
            role=User.Role.SECRETARIA,
            password='testpass123',
            is_active=True,
        )

        self.advisor = User.objects.create_user(
            document_number='ADV001',
            first_name='Asesor',
            last_name='Reparto',
            role=User.Role.ASESOR,
            password='testpass123',
            is_active=True,
        )

        self.student = User.objects.create_user(
            document_number='EST001',
            first_name='Estudiante',
            last_name='Reparto',
            role=User.Role.ESTUDIANTE,
            is_active=True,
            password='testpass123'
        )

        self.beneficiary = User.objects.create_user(
            document_number='BEN001',
            first_name='Beneficiario',
            last_name='Reparto',
            role=User.Role.BENEFICIARIO,
            password='testpass123'
        )

        self.case_complete = Case.objects.create(
            case_number='DIST-001',
            beneficiary=self.beneficiary,
            title='Caso Completo para Reparto',
            description='Descripción del caso completo',
            category=Case.CaseCategory.FAMILIA,
            status=Case.CaseStatus.SIN_ASIGNAR,
        )

        # Crear documentos válidos
        CaseDocument.objects.create(
            case=self.case_complete,
            document_type=CaseDocument.DocumentType.DOCUMENTO,
            file='test_file.pdf',
            is_valid=True,
        )
        CaseDocument.objects.create(
            case=self.case_complete,
            document_type=CaseDocument.DocumentType.RECIBO_SERVICIOS,
            file='test_file.pdf',
            is_valid=True,
        )
        CaseDocument.objects.create(
            case=self.case_complete,
            document_type=CaseDocument.DocumentType.FOTO,
            file='test_file.pdf',
            is_valid=True,
        )

    def test_solo_secretaria_puede_acceder_distribucion(self):
        """Verifica que solo Secretaría pueda acceder a la pantalla de reparto."""
        # Estudiante no puede acceder
        self.client.force_login(self.student)
        response = self.client.get(
            reverse('case_distribution', args=[self.case_complete.id]),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Reparto de Casos')

        # Secretaría sí puede acceder
        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse('case_distribution', args=[self.case_complete.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reparto de Casos')

    def test_advisor_can_access_distribution(self):
        """Verifica que los Asesores también pueden acceder."""
        self.client.force_login(self.advisor)
        response = self.client.get(
            reverse('case_distribution', args=[self.case_complete.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reparto de Casos')

    def test_vista_muestra_estado_completo(self):
        """Verifica que la vista muestra 'Completo' para un caso completo."""
        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse('case_distribution', args=[self.case_complete.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completo')

    def test_vista_muestra_estado_incompleto(self):
        """Verifica que la vista muestra 'Incompleto' para un caso sin documentos."""
        case_incomplete = Case.objects.create(
            case_number='DIST-002',
            beneficiary=self.beneficiary,
            title='Caso Incompleto',
            description='Descripción',
            category=Case.CaseCategory.CIVIL,
            status=Case.CaseStatus.SIN_ASIGNAR,
        )

        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse('case_distribution', args=[case_incomplete.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Incompleto')

    def test_asignacion_manual_exitosa(self):
        """Verifica que un caso completo se puede asignar manualmente."""
        self.client.force_login(self.secretary)

        response = self.client.post(
            reverse('case_distribution', args=[self.case_complete.id]),
            {
                'category': Case.CaseCategory.FAMILIA,
                'case_type': Case.FamiliaType.CONCEPTO,
                'assigned_student': self.student.id,
                'notes': 'Asignación de prueba',
            },
            follow=True
        )

        # Verificar que el caso fue asignado
        self.case_complete.refresh_from_db()
        self.assertEqual(self.case_complete.assigned_student, self.student)
        self.assertEqual(self.case_complete.status, Case.CaseStatus.ASIGNADO)

        # Verificar que se creó registro en CaseAssignment
        from cases.models import CaseAssignment
        assignment = CaseAssignment.objects.get(case=self.case_complete)
        self.assertEqual(assignment.assigned_student, self.student)
        self.assertEqual(assignment.assigned_advisor, self.secretary)

        # Verificar que se creó entrada en bitácora
        bitacora = BitacoraEntry.objects.get(
            case=self.case_complete,
            entry_type=BitacoraEntry.EntryType.CASO_ASIGNADO_MANUALMENTE
        )
        self.assertEqual(bitacora.author, self.secretary)

    def test_caso_incompleto_envio_revision(self):
        """Verifica que un caso incompleto se envía a revisión."""
        case_incomplete = Case.objects.create(
            case_number='DIST-003',
            beneficiary=self.beneficiary,
            title='Caso Incompleto',
            description='Descripción',
            category=Case.CaseCategory.LABORAL,
            status=Case.CaseStatus.SIN_ASIGNAR,
        )

        self.client.force_login(self.secretary)

        response = self.client.post(
            reverse('case_distribution', args=[case_incomplete.id]),
            {
                'reason': 'Falta documentación',
            },
            follow=True
        )

        # Verificar que el estado cambió a UNDER_REVIEW
        case_incomplete.refresh_from_db()
        self.assertIsNotNone(case_incomplete.assigned_student)
        self.assertEqual(case_incomplete.assigned_student.role, User.Role.ESTUDIANTE)
        self.assertEqual(case_incomplete.status, Case.CaseStatus.AUTOASIGNADO)
        self.assertEqual(case_incomplete.current_stage, Case.CaseStage.INFORMATION_GATHERING)

        # Verificar que se creó entrada en bitácora
        bitacora = BitacoraEntry.objects.get(
            case=case_incomplete,
            entry_type=BitacoraEntry.EntryType.CASO_ENVIADO_REVISION
        )
        self.assertIn('Falta documentación', bitacora.content)

    def test_caso_incompleto_con_estudiante_queda_autoasignado(self):
        """Si el caso ya viene de entrevista con estudiante, revision conserva autoasignacion."""
        case_incomplete = Case.objects.create(
            case_number='DIST-003-A',
            beneficiary=self.beneficiary,
            assigned_student=self.student,
            title='Caso Incompleto con Estudiante',
            description='Descripcion',
            category=Case.CaseCategory.LABORAL,
            status=Case.CaseStatus.SIN_ASIGNAR,
        )

        self.client.force_login(self.secretary)

        self.client.post(
            reverse('case_distribution', args=[case_incomplete.id]),
            {
                'reason': 'Falta documentacion tomada en entrevista',
            },
            follow=True
        )

        case_incomplete.refresh_from_db()
        self.assertEqual(case_incomplete.assigned_student, self.student)
        self.assertEqual(case_incomplete.status, Case.CaseStatus.AUTOASIGNADO)
        self.assertEqual(case_incomplete.current_stage, Case.CaseStage.INFORMATION_GATHERING)

    def test_caso_incompleto_con_entrevista_de_estudiante_se_autoasigna(self):
        """Si la primera entrevista fue registrada por un estudiante, revision lo conserva como responsable."""
        case_incomplete = Case.objects.create(
            case_number='DIST-003-B',
            beneficiary=self.beneficiary,
            title='Caso Incompleto con Entrevista',
            description='Descripcion',
            category=Case.CaseCategory.LABORAL,
            status=Case.CaseStatus.SIN_ASIGNAR,
        )
        BitacoraEntry.objects.create(
            case=case_incomplete,
            author=self.student,
            entry_type=BitacoraEntry.EntryType.ENTREVISTA,
            content='Entrevista inicial registrada por estudiante.',
        )

        self.client.force_login(self.secretary)

        self.client.post(
            reverse('case_distribution', args=[case_incomplete.id]),
            {
                'reason': 'Falta documentacion tomada en entrevista',
            },
            follow=True
        )

        case_incomplete.refresh_from_db()
        self.assertEqual(case_incomplete.assigned_student, self.student)
        self.assertEqual(case_incomplete.status, Case.CaseStatus.AUTOASIGNADO)
        self.assertEqual(case_incomplete.current_stage, Case.CaseStage.INFORMATION_GATHERING)

    def test_gestion_casos_filtra_solo_estados_operativos(self):
        """El filtro de estado de Gestion de Casos muestra solo los estados solicitados."""
        self.client.force_login(self.secretary)

        response = self.client.get(reverse('secretary_cases'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sin asignar')
        self.assertContains(response, 'Autoasignado')
        self.assertContains(response, 'Asignados / en proceso')
        self.assertNotContains(response, 'Esperar por beneficiario')
        self.assertNotContains(response, 'En revisi')
        self.assertContains(response, 'Asignar')

    def test_no_se_puede_asignar_caso_no_pending(self):
        """Verifica que no se pueda asignar un caso que no esté en PENDING_DISTRIBUTION."""
        self.case_complete.status = Case.CaseStatus.ASIGNADO
        self.case_complete.save()

        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse('case_distribution', args=[self.case_complete.id])
        )

        self.assertContains(response, 'no está disponible para reparto')

    def test_boton_asignar_habilitado_para_completo(self):
        """Verifica que el botón 'Asignar Caso' está habilitado para casos completos."""
        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse('case_distribution', args=[self.case_complete.id])
        )

        self.assertContains(response, 'Asignar Caso')
        # El botón NO debe tener disabled
        self.assertNotIn('disabled', response.content.decode().split('Asignar Caso')[0].split('<button')[-1])

    def test_boton_revision_habilitado_para_incompleto(self):
        """Verifica que el botón 'Enviar a Revisión' está para casos incompletos."""
        case_incomplete = Case.objects.create(
            case_number='DIST-004',
            beneficiary=self.beneficiary,
            title='Caso Incompleto',
            description='Descripción',
            category=Case.CaseCategory.PENAL,
            status=Case.CaseStatus.SIN_ASIGNAR,
        )

        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse('case_distribution', args=[case_incomplete.id])
        )

        self.assertContains(response, 'Enviar a Revisión')

    def test_validacion_campo_estudiante_requerido(self):
        """Verifica que el campo estudiante es obligatorio."""
        self.client.force_login(self.secretary)

        response = self.client.post(
            reverse('case_distribution', args=[self.case_complete.id]),
            {
                'category': Case.CaseCategory.FAMILIA,
                'case_type': Case.FamiliaType.CONCEPTO,
                'assigned_student': '',  # Campo vacío
                'notes': '',
            },
            follow=True
        )

        # El caso NO debe estar asignado
        self.case_complete.refresh_from_db()
        self.assertIsNone(self.case_complete.assigned_student)

    def test_trazabilidad_quién_asignó(self):
        """Verifica que se registra quién realizó la asignación."""
        self.client.force_login(self.secretary)

        self.client.post(
            reverse('case_distribution', args=[self.case_complete.id]),
            {
                'category': Case.CaseCategory.FAMILIA,
                'case_type': Case.FamiliaType.CONCEPTO,
                'assigned_student': self.student.id,
                'notes': '',
            },
        )

        # Verificar que la bitácora registra al usuario que asignó
        bitacora = BitacoraEntry.objects.get(
            case=self.case_complete,
            entry_type=BitacoraEntry.EntryType.CASO_ASIGNADO_MANUALMENTE
        )
        self.assertEqual(bitacora.author, self.secretary)
        self.assertIn(self.secretary.full_name, bitacora.content)

    def test_solo_secretaria_y_asesor_pueden_asignar(self):
        """Verifica control de acceso para asignación."""
        from cases.services import CaseDistributionService

        # Beneficiario NO puede asignar
        can_assign, _ = CaseDistributionService.can_assign_case(
            self.case_complete,
            self.beneficiary
        )
        self.assertFalse(can_assign)

        # Secretaría SÍ puede asignar
        can_assign, _ = CaseDistributionService.can_assign_case(
            self.case_complete,
            self.secretary
        )
        self.assertTrue(can_assign)

        # Asesor SÍ puede asignar
        can_assign, _ = CaseDistributionService.can_assign_case(
            self.case_complete,
            self.advisor
        )
        self.assertTrue(can_assign)


class CaseCalendarTests(TestCase):
    def setUp(self):
        self.secretary = User.objects.create_user(
            document_number="9000000001",
            password="123456",
            first_name="Martha",
            last_name="Gomez",
            role=User.Role.SECRETARIA,
            email="secretaria-calendar@example.com",
            is_active=True,
        )
        self.student = User.objects.create_user(
            document_number="9000000002",
            password="123456",
            first_name="Laura",
            last_name="Torres",
            role=User.Role.ESTUDIANTE,
            email="student-calendar@example.com",
            is_active=True,
        )
        self.advisor = User.objects.create_user(
            document_number="9000000003",
            password="123456",
            first_name="Elena",
            last_name="Restrepo",
            role=User.Role.ASESOR,
            email="advisor-calendar@example.com",
            is_active=True,
        )
        self.beneficiary = User.objects.create_user(
            document_number="9000000004",
            password="123456",
            first_name="Diana",
            last_name="Cortes",
            role=User.Role.BENEFICIARIO,
            email="beneficiary-calendar@example.com",
            is_active=True,
        )
        self.other_beneficiary = User.objects.create_user(
            document_number="9000000005",
            password="123456",
            first_name="Roberto",
            last_name="Mendoza",
            role=User.Role.BENEFICIARIO,
            email="beneficiary2-calendar@example.com",
            is_active=True,
        )
        self.case = Case.objects.create(
            case_number="CAL-001",
            title="Caso calendario principal",
            description="Caso principal para agenda",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.CONCEPTO,
            status=Case.CaseStatus.ASIGNADO,
            beneficiary=self.beneficiary,
            assigned_student=self.student,
            advisor=self.advisor,
            secretary=self.secretary,
        )
        self.other_case = Case.objects.create(
            case_number="CAL-002",
            title="Caso calendario secundario",
            description="Caso secundario para conflictos",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.CONCEPTO,
            status=Case.CaseStatus.ASIGNADO,
            beneficiary=self.other_beneficiary,
            assigned_student=self.student,
            advisor=self.advisor,
            secretary=self.secretary,
        )
        self.start = timezone.now() + timedelta(days=3)
        self.end = self.start + timedelta(hours=1)

    def test_student_calendar_shows_availability_and_busy_blocks(self):
        AdvisorAvailabilitySlot.objects.create(
            advisor=self.advisor,
            case=self.case,
            start_datetime=self.start,
            end_datetime=self.end,
        )
        CaseCalendarEvent.objects.create(
            case=self.other_case,
            created_by=self.advisor,
            event_type=CaseCalendarEvent.EventType.REUNION,
            title="Reunion de otro caso",
            start_datetime=self.start + timedelta(hours=2),
            end_datetime=self.start + timedelta(hours=3),
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("case_calendar_events", args=[self.case.id]))

        self.assertEqual(response.status_code, 200)
        event_ids = {item["id"] for item in response.json()}
        self.assertTrue(any(item.startswith("avail_") for item in event_ids))
        self.assertTrue(any(item.startswith("busy_cal_") for item in event_ids))

    def test_student_cannot_book_slot_when_other_case_conflicts(self):
        slot = AdvisorAvailabilitySlot.objects.create(
            advisor=self.advisor,
            case=self.case,
            start_datetime=self.start,
            end_datetime=self.end,
        )
        CaseCalendarEvent.objects.create(
            case=self.other_case,
            created_by=self.advisor,
            event_type=CaseCalendarEvent.EventType.REUNION,
            title="Reunion cruzada",
            start_datetime=self.start,
            end_datetime=self.end,
        )

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("case_meeting_invitation", args=[self.case.id, slot.id]),
            data="{}",
            content_type="application/json",
        )

        slot.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(slot.is_booked)

    def test_secretary_can_book_slot_and_notifies_participants(self):
        slot = AdvisorAvailabilitySlot.objects.create(
            advisor=self.advisor,
            case=self.case,
            start_datetime=self.start,
            end_datetime=self.end,
            teams_link="https://teams.microsoft.com/l/meetup-join/test",
        )

        self.client.force_login(self.secretary)
        response = self.client.post(
            reverse("case_meeting_invitation", args=[self.case.id, slot.id]),
            data='{"message": "Agenda solicitada por secretaria"}',
            content_type="application/json",
        )

        slot.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(slot.is_booked)
        self.assertEqual(slot.booked_by, self.secretary)
        self.assertTrue(Notification.objects.filter(recipient=self.student, case=self.case).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.advisor, case=self.case).exists())

    def test_advisor_cannot_create_overlapping_availability(self):
        AdvisorAvailabilitySlot.objects.create(
            advisor=self.advisor,
            case=self.other_case,
            start_datetime=self.start,
            end_datetime=self.end,
        )

        self.client.force_login(self.advisor)
        response = self.client.post(
            reverse("case_availability_create", args=[self.case.id]),
            data=json.dumps({
                "start_datetime": self.start.isoformat(),
                "end_datetime": self.end.isoformat(),
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
