from datetime import timedelta
from io import BytesIO

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone

from accounts.models import User
from accounts.services import run_deadline_check, run_inactivity_check
from cases.models import BitacoraEntry, Case, CaseDeadline, CaseDocument, Notification


class Command(BaseCommand):
    help = "Crea datos demo para probar usuarios, casos, bitÃ¡cora, deadlines y notificaciones."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Creando datos demo..."))

        # -------------------------------------------------
        # LIMPIEZA SEGURA DE DATOS DEMO
        # -------------------------------------------------
        Notification.objects.all().delete()
        CaseDeadline.objects.all().delete()
        BitacoraEntry.objects.all().delete()
        CaseDocument.objects.all().delete()
        Case.objects.all().delete()

        User.objects.filter(
            document_number__in=[
                "1001", "1002",   # secretarias
                "2001", "2002",   # asesores
                "3001", "3002", "3003", "3004", "3005",   # estudiantes
                "4001", "4002", "4003", "4004", "4005", "4006", "4007", "4008", "4009", "4010", "4011", "4012",  # beneficiarios
            ]
        ).delete()

        # -------------------------------------------------
        # USUARIOS
        # -------------------------------------------------
        secretaria1 = User.objects.create_user(
            document_number="1001",
            password="1234",
            first_name="Ana",
            last_name="Lopez",
            email="ana.secretaria@example.com",
            role=User.Role.SECRETARIA,
            is_active=True,
            is_staff=True,
        )

        secretaria2 = User.objects.create_user(
            document_number="1002",
            password="1234",
            first_name="Laura",
            last_name="Gomez",
            email="laura.secretaria@example.com",
            role=User.Role.SECRETARIA,
            is_active=True,
            is_staff=True,
        )

        asesor1 = User.objects.create_user(
            document_number="2001",
            password="1234",
            first_name="Roberto",
            last_name="Martinez",
            email="roberto.asesor@example.com",
            role=User.Role.ASESOR,
            is_active=True,
        )

        asesor2 = User.objects.create_user(
            document_number="2002",
            password="1234",
            first_name="Diana",
            last_name="Torres",
            email="diana.asesor@example.com",
            role=User.Role.ASESOR,
            is_active=True,
        )

        estudiante1 = User.objects.create_user(
            document_number="3001",
            password="1234",
            first_name="Carlos",
            last_name="Ramirez",
            email="carlos.estudiante@example.com",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )

        estudiante2 = User.objects.create_user(
            document_number="3002",
            password="1234",
            first_name="Valentina",
            last_name="Rojas",
            email="valentina.estudiante@example.com",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )
        
        estudiante3 = User.objects.create_user(
            document_number="3003",
            password="1234",
            first_name="Mateo",
            last_name="Silva",
            email="mateo.estudiante@example.com",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )

        estudiante4 = User.objects.create_user(
            document_number="3004",
            password="1234",
            first_name="Andrea",
            last_name="Moreno",
            email="andrea.estudiante@example.com",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )

        estudiante5 = User.objects.create_user(
            document_number="3005",
            password="1234",
            first_name="Felipe",
            last_name="Gutierrez",
            email="felipe.estudiante@example.com",
            role=User.Role.ESTUDIANTE,
            is_active=True,
        )

        beneficiario1 = User.objects.create_user(
            document_number="4001",
            password="1234",
            first_name="Maria",
            last_name="Perez",
            email="maria.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario2 = User.objects.create_user(
            document_number="4002",
            password="1234",
            first_name="Juan",
            last_name="Castro",
            email="juan.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario3 = User.objects.create_user(
            document_number="4003",
            password="1234",
            first_name="Elena",
            last_name="Moreno",
            email="elena.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario4 = User.objects.create_user(
            document_number="4004",
            password="1234",
            first_name="Carlos",
            last_name="Lopez",
            email="carlos.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario5 = User.objects.create_user(
            document_number="4005",
            password="1234",
            first_name="Teresa",
            last_name="Diaz",
            email="teresa.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario6 = User.objects.create_user(
            document_number="4006",
            password="1234",
            first_name="Antonio",
            last_name="Rodriguez",
            email="antonio.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario7 = User.objects.create_user(
            document_number="4007",
            password="1234",
            first_name="Patricia",
            last_name="Garcia",
            email="patricia.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario8 = User.objects.create_user(
            document_number="4008",
            password="1234",
            first_name="Diego",
            last_name="Martinez",
            email="diego.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario9 = User.objects.create_user(
            document_number="4009",
            password="1234",
            first_name="Sofia",
            last_name="Flores",
            email="sofia.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario10 = User.objects.create_user(
            document_number="4010",
            password="1234",
            first_name="David",
            last_name="Jimenez",
            email="david.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario11 = User.objects.create_user(
            document_number="4011",
            password="1234",
            first_name="Isabella",
            last_name="Vargas",
            email="isabella.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        beneficiario12 = User.objects.create_user(
            document_number="4012",
            password="1234",
            first_name="Roberto",
            last_name="Soto",
            email="roberto.beneficiario@example.com",
            role=User.Role.BENEFICIARIO,
            is_active=True,
        )

        # -------------------------------------------------
        # CASOS
        # -------------------------------------------------
        # CASOS EXISTENTES (compatibilidad)
        caso1 = Case.objects.create(
            case_number="00001",
            beneficiary=beneficiario1,
            assigned_student=estudiante1,
            advisor=asesor1,
            secretary=secretaria1,
            title="Caso laboral por despido",
            description="Consulta por posible despido sin justa causa.",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.PROCESO,
            status=Case.CaseStatus.ASIGNADO,
            current_stage=Case.CaseStage.ASSIGNMENT,
            phone="3000000001",
            address="Cali, Valle",
        )

        caso2 = Case.objects.create(
            case_number="00002",
            beneficiary=beneficiario2,
            assigned_student=estudiante2,
            advisor=asesor2,
            secretary=secretaria2,
            title="Caso de familia - custodia",
            description="Solicitud de orientaciÃ³n por custodia compartida.",
            category=Case.CaseCategory.FAMILIA,
            case_type_specific=Case.FamiliaType.PROCESO,
            status=Case.CaseStatus.EN_PROCESO,
            current_stage=Case.CaseStage.INFORMATION_GATHERING,
            phone="3000000002",
            address="Palmira, Valle",
        )

        caso3 = Case.objects.create(
            case_number="00003",
            beneficiary=beneficiario1,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Caso civil pendiente",
            description="Consulta sobre incumplimiento contractual.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.CONCEPTO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3000000003",
            address="Yumbo, Valle",
        )

        caso4 = Case.objects.create(
            case_number="00004",
            beneficiary=beneficiario2,
            assigned_student=estudiante1,
            advisor=asesor1,
            secretary=secretaria2,
            title="Caso penal autoasignado desde entrevista",
            description="Caso tomado por el estudiante desde la entrevista inicial; requiere seguimiento documental.",
            category=Case.CaseCategory.PENAL,
            case_type_specific=Case.PenalType.PROCESO,
            status=Case.CaseStatus.AUTOASIGNADO,
            current_stage=Case.CaseStage.INFORMATION_GATHERING,
            phone="3000000004",
            address="JamundÃ­, Valle",
        )

        # -------------------------------------------------
        # 4 CASOS COMPLETOS SIN ASIGNAR (PARA REPARTO MANUAL)
        # -------------------------------------------------
        caso_completo_1 = Case.objects.create(
            case_number="00005",
            beneficiary=beneficiario3,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Demanda civil por escrituraciÃ³n de propiedad",
            description="Caso civil completo sobre incumplimiento en escrituraciÃ³n de propiedad inmueble. Todas las pruebas disponibles.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3001112233",
            address="Cali, Barrio Granada",
        )

        caso_completo_2 = Case.objects.create(
            case_number="00006",
            beneficiary=beneficiario4,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Caso laboral por acoso en el trabajo",
            description="Demanda laboral por ambiente hostil y acoso. DocumentaciÃ³n completa aportada.",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.TUTELA,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3002223344",
            address="Cali, Barrio San Alejo",
        )

        caso_completo_3 = Case.objects.create(
            case_number="00007",
            beneficiary=beneficiario5,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de derecho penal - defensa en juicio",
            description="Caso penal con todos los documentos y pruebas disponibles para defensa.",
            category=Case.CaseCategory.PENAL,
            case_type_specific=Case.PenalType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3003334455",
            address="Palmira, Centro",
        )

        caso_completo_4 = Case.objects.create(
            case_number="00008",
            beneficiary=beneficiario6,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Asunto de derecho administrativo - derecho de peticiÃ³n",
            description="Caso administrativo con documentaciÃ³n completa para solicitud ante entidad pÃºblica.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.CONCEPTO_DP,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3004445566",
            address="Yumbo, Sur",
        )

        # 4 CASOS COMPLETOS ADICIONALES SIN ASIGNAR
        # -------------------------------------------------
        caso_completo_5 = Case.objects.create(
            case_number="00009",
            beneficiary=beneficiario11,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Demanda por incumplimiento de contrato comercial",
            description="Caso civil con documentaciÃ³n completa incluyendo contrato, facturas y pruebas de incumplimiento.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.CONCEPTO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3009990011",
            address="Cali, Barrio Centro",
        )

        caso_completo_6 = Case.objects.create(
            case_number="00010",
            beneficiary=beneficiario12,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria1,
            title="Caso laboral - liquidaciÃ³n de beneficios",
            description="Demanda por liquidaciÃ³n de prestaciones sociales. DocumentaciÃ³n completa disponible.",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.LIQUIDACION,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3009991111",
            address="Palmira, Barrio Santa Isabel",
        )

        caso_completo_7 = Case.objects.create(
            case_number="00011",
            beneficiary=beneficiario3,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria2,
            title="Asunto de migraciÃ³n - solicitud de permiso de residencia",
            description="Caso de derecho pÃºblico sobre derechos de migrantes con documentaciÃ³n de migraciÃ³n.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.SOLICITUD_REFUGIO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3009992222",
            address="Cali, Barrio Puerto",
        )

        caso_completo_8 = Case.objects.create(
            case_number="00012",
            beneficiary=beneficiario4,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de derecho penal - defensa preventiva",
            description="Caso penal preventivo con anÃ¡lisis jurÃ­dico completo y documentaciÃ³n de apoyo.",
            category=Case.CaseCategory.PENAL,
            case_type_specific=Case.PenalType.CONCEPTO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3009993333",
            address="JamundÃ­, Centro",
        )

        caso_completo_9 = Case.objects.create(
            case_number="00013",
            beneficiary=beneficiario1,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de propiedad intelectual - derechos de autor",
            description="Caso sobre protecciÃ³n de derechos de autor con documentaciÃ³n completa.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3001114444",
            address="Cali, Barrio Granada",
        )

        caso_completo_10 = Case.objects.create(
            case_number="00014",
            beneficiary=beneficiario2,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de acceso a informaciÃ³n pÃºblica",
            description="Caso de accountability basado en solicitud de acceso a informaciÃ³n.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.CONCEPTO_DP,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3002225555",
            address="Cali, Barrio El PeÃ±ol",
        )

        caso_completo_11 = Case.objects.create(
            case_number="00015",
            beneficiary=beneficiario3,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de violencia intrafamiliar - medidas de protecciÃ³n",
            description="Caso de violencia intrafamiliar con solicitud de medidas cautelares.",
            category=Case.CaseCategory.FAMILIA,
            case_type_specific=Case.FamiliaType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3003336666",
            address="Cali, Barrio Javeriana",
        )

        caso_completo_12 = Case.objects.create(
            case_number="00016",
            beneficiary=beneficiario4,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de sucesiÃ³n hereditaria - divisiÃ³n de bienes",
            description="Caso de sucesiÃ³n con documentaciÃ³n completa de bienes e inventarios.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3004447777",
            address="Cali, Barrio San Fernando",
        )

        caso_completo_13 = Case.objects.create(
            case_number="00017",
            beneficiary=beneficiario5,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de tutela constitucional - derechos fundamentales",
            description="Caso de tutela con fundamentos legales y pruebas documentales.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.CONCEPTO_DP,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3005558888",
            address="Cali, Barrio El Lili",
        )

        caso_completo_14 = Case.objects.create(
            case_number="00018",
            beneficiary=beneficiario6,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de derecho laboral - despido injustificado",
            description="Caso laboral por despido con documentaciÃ³n de contrato y comunicaciones.",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.LIQUIDACION,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3006669999",
            address="Cali, Barrio Santa Teresita",
        )

        caso_completo_15 = Case.objects.create(
            case_number="00019",
            beneficiary=beneficiario7,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta penal - querella por difamaciÃ³n",
            description="Caso penal con pruebas de comunicaciones y testimonios documentados.",
            category=Case.CaseCategory.PENAL,
            case_type_specific=Case.PenalType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3007770000",
            address="Cali, Barrio Pensiones",
        )

        caso_completo_16 = Case.objects.create(
            case_number="00020",
            beneficiary=beneficiario1,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de compraventa de inmueble",
            description="Caso civil de compraventa con documentaciÃ³n de pago y transferencia.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3001111111",
            address="Cali, Barrio CristÃ³bal ColÃ³n",
        )

        caso_completo_17 = Case.objects.create(
            case_number="00021",
            beneficiary=beneficiario2,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de tutela por salud - medicamentos",
            description="Caso de tutela por derecho a la salud con prescripciones mÃ©dicas.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.CONCEPTO_DP,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3002222222",
            address="Cali, Barrio Floralia",
        )

        caso_completo_18 = Case.objects.create(
            case_number="00022",
            beneficiary=beneficiario3,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta laboral - acoso sexual en el trabajo",
            description="Caso laboral por acoso sexual con testimonios y pruebas documentadas.",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3003333333",
            address="Cali, Barrio San Alejo",
        )

        caso_completo_19 = Case.objects.create(
            case_number="00023",
            beneficiary=beneficiario4,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta penal - fraude electrÃ³nico",
            description="Caso de fraude electrÃ³nico con pruebas de transacciones irregulares.",
            category=Case.CaseCategory.PENAL,
            case_type_specific=Case.PenalType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3004444444",
            address="Cali, Barrio MelÃ©ndez",
        )

        caso_completo_20 = Case.objects.create(
            case_number="00024",
            beneficiary=beneficiario5,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de divorcio y custodia de menores",
            description="Caso de divorcio con soluciÃ³n de custodia e informaciÃ³n de hijos.",
            category=Case.CaseCategory.FAMILIA,
            case_type_specific=Case.FamiliaType.CONCEPTO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3005555555",
            address="Cali, Barrio Chipichape",
        )

        caso_completo_21 = Case.objects.create(
            case_number="00025",
            beneficiary=beneficiario6,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de desalojo por falta de pago",
            description="Caso de desalojo con documentaciÃ³n de contratos de arrendamiento y deudas.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3006666666",
            address="Cali, Barrio Ciudadela Comfandi",
        )

        caso_completo_22 = Case.objects.create(
            case_number="00026",
            beneficiary=beneficiario7,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de reconocimiento de paternidad",
            description="Caso de reconocimiento de paternidad con pruebas biolÃ³gicas y documentos.",
            category=Case.CaseCategory.FAMILIA,
            case_type_specific=Case.FamiliaType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3007777777",
            address="Cali, Barrio Eduardo Santos",
        )

        caso_completo_23 = Case.objects.create(
            case_number="00031",
            beneficiary=beneficiario1,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta de negligencia mÃ©dica",
            description="Caso de negligencia mÃ©dica con informes clÃ­nicos e histÃ³ricos mÃ©dicos.",
            category=Case.CaseCategory.PENAL,
            case_type_specific=Case.PenalType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3008888888",
            address="Cali, Barrio El PeÃ±ol",
        )

        caso_completo_24 = Case.objects.create(
            case_number="00032",
            beneficiary=beneficiario2,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Consulta de reparaciÃ³n de daÃ±o ambiental",
            description="Caso de daÃ±o ambiental con peritos ambientales y reportes tÃ©cnicos.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.CONCEPTO_DP,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3009999999",
            address="Cali, Barrio El Calvario",
        )

        # -------------------------------------------------
        # 4 CASOS INCOMPLETOS SIN ASIGNAR (PARA ENVIAR A REVISION)
        # -------------------------------------------------
        caso_incompleto_1 = Case.objects.create(
            case_number="00027",
            beneficiary=beneficiario7,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta familia - pensiÃ³n alimentaria",
            description="Caso de pensiÃ³n alimentaria sin documentaciÃ³n completa.",
            category=Case.CaseCategory.FAMILIA,
            case_type_specific=Case.FamiliaType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3005556677",
            address="JamundÃ­",
        )

        caso_incompleto_2 = Case.objects.create(
            case_number="00028",
            beneficiary=beneficiario8,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Caso laboral en etapa inicial",
            description="Demanda laboral que requiere mÃ¡s documentaciÃ³n del empleador.",
            category=Case.CaseCategory.LABORAL,
            case_type_specific=Case.LaboralType.PROCESO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3006667788",
            address="Cali, Barrio Ciudad 2000",
        )

        caso_incompleto_3 = Case.objects.create(
            case_number="00029",
            beneficiary=beneficiario9,
            assigned_student=None,
            advisor=asesor1,
            secretary=secretaria1,
            title="Consulta civil - herencia sin liquidar",
            description="Caso civil sobre herencia que necesita documentos del notario.",
            category=Case.CaseCategory.CIVIL,
            case_type_specific=Case.CivilType.CONCEPTO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3007778899",
            address="Palmira, Barrio El Pilar",
        )

        caso_incompleto_4 = Case.objects.create(
            case_number="00030",
            beneficiary=beneficiario10,
            assigned_student=None,
            advisor=asesor2,
            secretary=secretaria2,
            title="Caso pÃºblico - derechos de migrantes",
            description="Caso de migraciÃ³n en proceso inicial, falta documentaciÃ³n de identidad.",
            category=Case.CaseCategory.DERECHO_PUBLICO_MIGRANTES,
            case_type_specific=Case.DerechoPublicoMigrantesType.SOLICITUD_REFUGIO,
            status=Case.CaseStatus.SIN_ASIGNAR,
            current_stage=Case.CaseStage.UNASSIGNED,
            phone="3008889900",
            address="Cali, Puerto",
        )

        now = timezone.now()

        # -------------------------------------------------
        # DOCUMENTOS PARA CASOS COMPLETOS
        # -------------------------------------------------
        # Helper function para crear archivos demo
        def create_demo_file(name, content):
            return ContentFile(content.encode('utf-8'), name=name)

        # Documentos para caso_completo_1
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "escritura_propiedad.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_asesoramiento.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_fisica.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_1,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_2
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "contrato_laboral.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_consulta.pdf"),
            (CaseDocument.DocumentType.FOTO, "evidencia_acoso.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_2,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_3
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "denuncia_penal.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_defensa.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_fisica_penal.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_3,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_4
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "derechos_de_peticion.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_gestion.pdf"),
            (CaseDocument.DocumentType.FOTO, "certificado_entidad.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_4,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_5
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "contrato_comercial.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_contractual.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_incumplimiento.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_5,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_6
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "acta_liquidacion.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_liquidacion.pdf"),
            (CaseDocument.DocumentType.FOTO, "comprobante_beneficios.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_6,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_7
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "solicitud_migracion.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_migracion.pdf"),
            (CaseDocument.DocumentType.FOTO, "documento_identidad.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_7,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_8
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "defensa_penal.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_defensa.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_defensa.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_8,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_9
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "derechos_autor.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_autor.pdf"),
            (CaseDocument.DocumentType.FOTO, "evidencia_autor.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_9,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_10
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "solicitud_info.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_info.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_info.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_10,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_11
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "violencia_intrafamiliar.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_violencia.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_violencia.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_11,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_12
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "sucesion_hereditaria.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_sucesion.pdf"),
            (CaseDocument.DocumentType.FOTO, "inventario_bienes.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_12,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_13
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "tutela_constitucional.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_tutela.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_tutela.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_13,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_14
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "despido_injustificado.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_laboral.pdf"),
            (CaseDocument.DocumentType.FOTO, "contrato_laboral.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_14,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_15
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "querella_difamacion.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_penal.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_penal.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_15,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_16
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "compraventa_inmueble.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_compraventa.pdf"),
            (CaseDocument.DocumentType.FOTO, "titulo_propiedad.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_16,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_17
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "tutela_salud.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_salud.pdf"),
            (CaseDocument.DocumentType.FOTO, "prescripcion_medica.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_17,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_18
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "acoso_sexual.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_acoso.pdf"),
            (CaseDocument.DocumentType.FOTO, "testimonio_acoso.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_18,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_19
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "fraude_electronico.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_fraude.pdf"),
            (CaseDocument.DocumentType.FOTO, "transacciones_fraude.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_19,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_20
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "divorcio_custodia.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_familia.pdf"),
            (CaseDocument.DocumentType.FOTO, "acta_nacimiento.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_20,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_21
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "desalojo_pago.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_desalojo.pdf"),
            (CaseDocument.DocumentType.FOTO, "contrato_arrendamiento.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_21,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_22
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "reconocimiento_paternidad.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_paternidad.pdf"),
            (CaseDocument.DocumentType.FOTO, "prueba_biologica.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_22,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos para caso_completo_23
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "negligencia_medica.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_medico.pdf"),
            (CaseDocument.DocumentType.FOTO, "historial_clinico.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_23,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria1,
            )

        # Documentos para caso_completo_24
        for doc_type, doc_name in [
            (CaseDocument.DocumentType.DOCUMENTO, "daÃ±o_ambiental.pdf"),
            (CaseDocument.DocumentType.RECIBO_SERVICIOS, "recibo_ambiental.pdf"),
            (CaseDocument.DocumentType.FOTO, "reporte_pericial.jpg"),
        ]:
            doc = CaseDocument.objects.create(
                case=caso_completo_24,
                document_type=doc_type,
                file=create_demo_file(doc_name, f"Contenido demo para {doc_name}"),
                original_name=doc_name,
                is_valid=True,
                uploaded_by=secretaria2,
            )

        # Documentos incompletos para casos incompletos (solo 1-2 documentos)
        # caso_incompleto_1: solo documento y foto (falta recibo)
        CaseDocument.objects.create(
            case=caso_incompleto_1,
            document_type=CaseDocument.DocumentType.DOCUMENTO,
            file=create_demo_file("solicitud.pdf", "Contenido demo"),
            original_name="solicitud.pdf",
            is_valid=True,
            uploaded_by=secretaria1,
        )
        CaseDocument.objects.create(
            case=caso_incompleto_1,
            document_type=CaseDocument.DocumentType.FOTO,
            file=create_demo_file("prueba.jpg", "Contenido demo"),
            original_name="prueba.jpg",
            is_valid=True,
            uploaded_by=secretaria1,
        )

        # caso_incompleto_2: solo documento (faltan recibo y foto)
        CaseDocument.objects.create(
            case=caso_incompleto_2,
            document_type=CaseDocument.DocumentType.DOCUMENTO,
            file=create_demo_file("demanda.pdf", "Contenido demo"),
            original_name="demanda.pdf",
            is_valid=True,
            uploaded_by=secretaria2,
        )

        # caso_incompleto_3: documento y recibo (falta foto)
        CaseDocument.objects.create(
            case=caso_incompleto_3,
            document_type=CaseDocument.DocumentType.DOCUMENTO,
            file=create_demo_file("testamento.pdf", "Contenido demo"),
            original_name="testamento.pdf",
            is_valid=True,
            uploaded_by=secretaria1,
        )
        CaseDocument.objects.create(
            case=caso_incompleto_3,
            document_type=CaseDocument.DocumentType.RECIBO_SERVICIOS,
            file=create_demo_file("recibo.pdf", "Contenido demo"),
            original_name="recibo.pdf",
            is_valid=True,
            uploaded_by=secretaria1,
        )

        # caso_incompleto_4: solo documento (faltan recibo y foto)
        CaseDocument.objects.create(
            case=caso_incompleto_4,
            document_type=CaseDocument.DocumentType.DOCUMENTO,
            file=create_demo_file("pasaporte.pdf", "Contenido demo"),
            original_name="pasaporte.pdf",
            is_valid=True,
            uploaded_by=secretaria2,
        )

        # -------------------------------------------------
        # BITÃCORA
        # -------------------------------------------------
        entrada1 = BitacoraEntry.objects.create(
            case=caso1,
            author=secretaria1,
            entry_type=BitacoraEntry.EntryType.ASIGNACION,
            content="Caso asignado al estudiante Carlos RamÃ­rez.",
            notify=False,
        )

        entrada2 = BitacoraEntry.objects.create(
            case=caso2,
            author=estudiante2,
            entry_type=BitacoraEntry.EntryType.ACTUALIZACION,
            content="Se realizÃ³ entrevista inicial con el beneficiario.",
            notify=False,
        )

        entrada3 = BitacoraEntry.objects.create(
            case=caso4,
            author=asesor1,
            entry_type=BitacoraEntry.EntryType.DOCUMENTO,
            content="Se revisÃ³ documentaciÃ³n inicial aportada.",
            notify=False,
        )

        # Forzar fechas viejas / recientes
        BitacoraEntry.objects.filter(id=entrada1.id).update(created_at=now - timedelta(days=10))
        BitacoraEntry.objects.filter(id=entrada2.id).update(created_at=now - timedelta(days=1))
        BitacoraEntry.objects.filter(id=entrada3.id).update(created_at=now - timedelta(days=8))

        Case.objects.filter(id=caso1.id).update(updated_at=now - timedelta(days=10))
        Case.objects.filter(id=caso2.id).update(updated_at=now - timedelta(days=1))
        Case.objects.filter(id=caso3.id).update(updated_at=now - timedelta(days=2))
        Case.objects.filter(id=caso4.id).update(updated_at=now - timedelta(days=8))

        caso1.refresh_from_db()
        caso2.refresh_from_db()
        caso3.refresh_from_db()
        caso4.refresh_from_db()

        # -------------------------------------------------
        # FECHAS LÃMITE
        # -------------------------------------------------
        CaseDeadline.objects.create(
            case=caso1,
            created_by=secretaria1,
            title="Entrega de documentos laborales",
            description="Debe entregarse soporte documental del despido.",
            due_date=now + timedelta(days=1),
            is_completed=False,
        )

        CaseDeadline.objects.create(
            case=caso2,
            created_by=asesor2,
            title="Audiencia preliminar",
            description="PreparaciÃ³n para audiencia preliminar.",
            due_date=now,
            is_completed=False,
        )

        CaseDeadline.objects.create(
            case=caso4,
            created_by=secretaria2,
            title="TÃ©rmino procesal vencido",
            description="Fecha procesal ya vencida para pruebas.",
            due_date=now - timedelta(days=2),
            is_completed=False,
        )

        # -------------------------------------------------
        # GENERAR NOTIFICACIONES
        # -------------------------------------------------
        run_inactivity_check()
        run_deadline_check()

        # -------------------------------------------------
        # RESUMEN
        # -------------------------------------------------
        self.stdout.write(self.style.SUCCESS("Datos demo creados correctamente."))
        self.stdout.write("")
        self.stdout.write("USUARIOS (Login):") 
        self.stdout.write("  SecretarÃ­a 1     -> 1001 / 1234")
        self.stdout.write("  SecretarÃ­a 2     -> 1002 / 1234")
        self.stdout.write("  Asesor 1         -> 2001 / 1234")
        self.stdout.write("  Asesor 2         -> 2002 / 1234")
        self.stdout.write("  Estudiante 1     -> 3001 / 1234")
        self.stdout.write("  Estudiante 2     -> 3002 / 1234")
        self.stdout.write("  Estudiante 3     -> 3003 / 1234")
        self.stdout.write("  Estudiante 4     -> 3004 / 1234")
        self.stdout.write("  Estudiante 5     -> 3005 / 1234")
        self.stdout.write("  Beneficiario 1   -> 4001 / 1234")
        self.stdout.write("")
        self.stdout.write("CASOS PARA REPARTO MANUAL:")
        self.stdout.write("  âœ“ 24 CASOS COMPLETOS (SIN ASIGNAR):")
        self.stdout.write("    - CASO-2026-010: Demanda civil por escrituraciÃ³n")
        self.stdout.write("    - CASO-2026-020: Caso laboral por acoso")
        self.stdout.write("    - CASO-2026-030: Defensa penal")
        self.stdout.write("    - CASO-2026-040: Derecho administrativo")
        self.stdout.write("    - CASO-2026-090: Incumplimiento de contrato")
        self.stdout.write("    - CASO-2026-100: LiquidaciÃ³n de beneficios")
        self.stdout.write("    - CASO-2026-110: Solicitud de migraciÃ³n")
        self.stdout.write("    - CASO-2026-120: Defensa penal disciplinaria")
        self.stdout.write("    - CASO-2026-130: Propiedad intelectual - derechos de autor")
        self.stdout.write("    - CASO-2026-140: Acceso a informaciÃ³n pÃºblica")
        self.stdout.write("    - CASO-2026-150: Violencia intrafamiliar")
        self.stdout.write("    - CASO-2026-160: SucesiÃ³n hereditaria - divisiÃ³n de bienes")
        self.stdout.write("    - CASO-2026-170: Tutela constitucional - derechos fundamentales")
        self.stdout.write("    - CASO-2026-180: Derecho laboral - despido injustificado")
        self.stdout.write("    - CASO-2026-190: Penal - querella por difamaciÃ³n")
        self.stdout.write("    - CASO-2026-200: Compraventa de inmueble")
        self.stdout.write("    - CASO-2026-210: Tutela por salud - medicamentos")
        self.stdout.write("    - CASO-2026-220: Laboral - acoso sexual en el trabajo")
        self.stdout.write("    - CASO-2026-230: Penal - fraude electrÃ³nico")
        self.stdout.write("    - CASO-2026-240: Familia - divorcio y custodia de menores")
        self.stdout.write("    - CASO-2026-250: Desalojo por falta de pago")
        self.stdout.write("    - CASO-2026-260: Reconocimiento de paternidad")
        self.stdout.write("    - CASO-2026-270: Negligencia mÃ©dica")
        self.stdout.write("    - CASO-2026-280: ReparaciÃ³n de daÃ±o ambiental")
        self.stdout.write("")
        self.stdout.write("  âš  4 CASOS INCOMPLETOS (SIN ASIGNAR - PARA ENVIAR A REVISIÃ“N):")
        self.stdout.write("    - CASO-2026-050: PensiÃ³n alimentaria (falta recibo)")
        self.stdout.write("    - CASO-2026-060: Laboral en etapa inicial (faltan recibo y foto)")
        self.stdout.write("    - CASO-2026-070: Herencia (falta foto)")
        self.stdout.write("    - CASO-2026-080: Derechos de migrantes (faltan recibo y foto)")
        self.stdout.write("")

        # -------------------------------------------------
        # ASIGNAR NÃšMEROS SECUENCIALES
        # -------------------------------------------------
        # Asignar sequence_number basado en case_number ordenado
        cases_ordered = Case.objects.all().order_by('case_number')
        for seq_num, case in enumerate(cases_ordered, start=1):
            case.sequence_number = seq_num
            case.save(update_fields=['sequence_number'])

        self.stdout.write(f"Resumen: {Case.objects.count()} casos creados")
        self.stdout.write(f"  - {CaseDocument.objects.count()} documentos")
        self.stdout.write(f"  - {BitacoraEntry.objects.count()} bitÃ¡coras")
        self.stdout.write(f"  - {CaseDeadline.objects.count()} deadlines")
        self.stdout.write(f"  - {Notification.objects.count()} notificaciones")
