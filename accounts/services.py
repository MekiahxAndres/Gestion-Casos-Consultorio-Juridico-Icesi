import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail

from cases.models import BitacoraEntry, Case
from cases.models import Notification, CaseDeadline

logger = logging.getLogger(__name__)


INACTIVITY_DAYS = 7


# =========================================================
# INACTIVIDAD
# =========================================================

def get_last_case_activity(case_obj):
    last_entry = case_obj.bitacora_entries.order_by("-created_at").first()

    if last_entry:
        return last_entry.created_at

    return case_obj.updated_at


def build_inactivity_message(case_obj, last_activity):
    days_inactive = (timezone.now() - last_activity).days

    return {
        "title": "Caso sin actividad reciente",
        "message": (
            f"El caso {case_obj.case_number} lleva {days_inactive} días sin actividad registrada."
        ),
    }


def create_notification_if_needed(recipient, case_obj, title, message):
    already_exists = Notification.objects.filter(
        recipient=recipient,
        case=case_obj,
        notification_type=Notification.NotificationType.INACTIVITY,
        is_resolved=False,
    ).exists()

    if not already_exists:
        Notification.objects.create(
            recipient=recipient,
            case=case_obj,
            notification_type=Notification.NotificationType.INACTIVITY,
            title=title,
            message=message,
        )


def resolve_inactivity_notifications(case_obj):
    Notification.objects.filter(
        case=case_obj,
        notification_type=Notification.NotificationType.INACTIVITY,
        is_resolved=False,
    ).update(is_resolved=True)


def check_case_inactivity(case_obj):
    last_activity = get_last_case_activity(case_obj)
    limit_date = timezone.now() - timedelta(days=INACTIVITY_DAYS)

    if last_activity <= limit_date:
        data = build_inactivity_message(case_obj, last_activity)

        recipients = [
            getattr(case_obj, "assigned_student", None),
            getattr(case_obj, "advisor", None),
            getattr(case_obj, "secretary", None),
        ]

        recipients = list(filter(None, set(recipients)))  # 🔥 evita duplicados

        for recipient in recipients:
            create_notification_if_needed(
                recipient=recipient,
                case_obj=case_obj,
                title=data["title"],
                message=data["message"],
            )
    else:
        resolve_inactivity_notifications(case_obj)


def run_inactivity_check():
    cases = Case.objects.all().prefetch_related("bitacora_entries")
    for case_obj in cases:
        check_case_inactivity(case_obj)


# =========================================================
# FECHAS LÍMITE
# =========================================================

def build_deadline_message(deadline, days_remaining):
    formatted_date = deadline.due_date.strftime("%d/%m/%Y %I:%M %p")

    if days_remaining < 0:
        return {
            "title": "Fecha límite vencida",
            "message": (
                f"El caso {deadline.case.case_number} tenía como fecha límite '{deadline.title}' "
                f"el {formatted_date} y ya venció hace {abs(days_remaining)} día(s)."
            ),
        }

    if days_remaining == 0:
        return {
            "title": "Fecha límite hoy",
            "message": (
                f"El caso {deadline.case.case_number} tiene la fecha límite '{deadline.title}' "
                f"para hoy ({formatted_date})."
            ),
        }

    if days_remaining == 1:
        return {
            "title": "Fecha límite mañana",
            "message": (
                f"El caso {deadline.case.case_number} tiene la fecha límite '{deadline.title}' "
                f"para mañana ({formatted_date})."
            ),
        }

    return {
        "title": "Fecha límite próxima",
        "message": (
            f"El caso {deadline.case.case_number} tiene la fecha límite '{deadline.title}' "
            f"el {formatted_date}, es decir, en {days_remaining} días."
        ),
    }


def create_deadline_notification_if_needed(recipient, deadline, title, message):
    already_exists = Notification.objects.filter(
        recipient=recipient,
        case=deadline.case,
        deadline=deadline,
        notification_type=Notification.NotificationType.DEADLINE,
        title=title,
        is_resolved=False,
    ).exists()

    if not already_exists:
        Notification.objects.create(
            recipient=recipient,
            case=deadline.case,
            deadline=deadline,
            notification_type=Notification.NotificationType.DEADLINE,
            title=title,
            message=message,
        )


def resolve_deadline_notifications(deadline):
    Notification.objects.filter(
        deadline=deadline,
        notification_type=Notification.NotificationType.DEADLINE,
        is_resolved=False,
    ).update(is_resolved=True)


def check_single_deadline(deadline):
    if deadline.is_completed:
        resolve_deadline_notifications(deadline)
        return

    now = timezone.now()
    days_remaining = (deadline.due_date.date() - now.date()).days

    if days_remaining <= 3:
        data = build_deadline_message(deadline, days_remaining)

        Notification.objects.filter(
            deadline=deadline,
            notification_type=Notification.NotificationType.DEADLINE,
            is_resolved=False,
        ).exclude(title=data["title"]).update(is_resolved=True)

        recipients = [
            getattr(deadline.case, "assigned_student", None),
            getattr(deadline.case, "advisor", None),
            getattr(deadline.case, "secretary", None),
        ]

        recipients = list(filter(None, set(recipients)))  # 🔥 evita duplicados

        for recipient in recipients:
            create_deadline_notification_if_needed(
                recipient=recipient,
                deadline=deadline,
                title=data["title"],
                message=data["message"],
            )
    else:
        resolve_deadline_notifications(deadline)


def run_deadline_check():
    deadlines = CaseDeadline.objects.filter(is_completed=False).select_related("case")
    for deadline in deadlines:
        check_single_deadline(deadline)


# =========================================================
# CONSULTA
# =========================================================

def get_notifications_for_user(user, notification_type=None):
    queryset = Notification.objects.filter(
        recipient=user,
        is_resolved=False,
    ).select_related("case", "deadline", "related_document", "related_entry").order_by("-created_at")

    if notification_type and notification_type != "ALL":
        queryset = queryset.filter(notification_type=notification_type)

    return queryset


# =========================================================
# DOCUMENTOS SUBIDOS
# =========================================================

def build_document_upload_message(document):
    case_obj = document.entry.case
    author_name = getattr(document.entry.author, "full_name", None) or "Un usuario"
    document_name = document.original_name or document.file.name

    return {
        "title": "Documento subido al caso",
        "message": (
            f"{author_name} subió el documento '{document_name}' "
            f"al caso {case_obj.case_number}."
        ),
    }


def notify_advisor_document_uploaded(document):
    """
    Notifica al asesor asignado cuando se adjunta un documento a la bitácora.
    Si el caso no tiene asesor, deja registro interno y no crea notificación.
    """
    case_obj = document.entry.case
    advisor = getattr(case_obj, "advisor", None)
    document_name = document.original_name or document.file.name

    if not advisor:
        BitacoraEntry.objects.create(
            case=case_obj,
            author=document.entry.author,
            entry_type=BitacoraEntry.EntryType.EVENTO,
            content=(
                "Alerta no enviada: el caso no tiene asesor asignado "
                f"para el documento '{document_name}'."
            ),
        )
        return None

    data = build_document_upload_message(document)
    notification, _ = Notification.objects.get_or_create(
        recipient=advisor,
        case=case_obj,
        related_document=document,
        notification_type=Notification.NotificationType.DOCUMENT_UPLOAD,
        defaults={
            "title": data["title"],
            "message": data["message"],
        },
    )
    return notification


# =========================================================
# EVENTOS IMPORTANTES
# =========================================================

def build_important_event_message(entry):
    case_obj = entry.case
    author_name = getattr(entry.author, "full_name", None) or "Un usuario"
    scheduled_text = ""

    if entry.scheduled_for:
        scheduled_text = f" Fecha del evento: {entry.scheduled_for.strftime('%d/%m/%Y %I:%M %p')}."

    return {
        "title": "Evento importante registrado",
        "message": (
            f"{author_name} registró un evento importante en el caso {case_obj.case_number}: "
            f"{entry.content}{scheduled_text}"
        ),
    }


def notify_advisor_important_event(entry):
    """
    Notifica al asesor asignado cuando se registra un evento importante en bitácora.
    Si el caso no tiene asesor, deja registro interno y no crea notificación.
    """
    case_obj = entry.case
    advisor = getattr(case_obj, "advisor", None)

    if not advisor:
        BitacoraEntry.objects.create(
            case=case_obj,
            author=entry.author,
            entry_type=BitacoraEntry.EntryType.EVENTO,
            content=(
                "Alerta no enviada: el caso no tiene asesor asignado "
                "para el evento importante registrado."
            ),
        )
        return None

    data = build_important_event_message(entry)
    notification, _ = Notification.objects.get_or_create(
        recipient=advisor,
        case=case_obj,
        related_entry=entry,
        notification_type=Notification.NotificationType.IMPORTANT_EVENT,
        defaults={
            "title": data["title"],
            "message": data["message"],
        },
    )
    return notification


# =========================================================
# ENTRADAS DE BITÁCORA
# =========================================================

def get_case_participants(case_obj, exclude_user=None):
    recipients = [
        getattr(case_obj, "assigned_student", None),
        getattr(case_obj, "advisor", None),
        getattr(case_obj, "secretary", None),
    ]

    unique_recipients = []
    seen_ids = set()
    exclude_id = getattr(exclude_user, "id", None)

    for recipient in recipients:
        if not recipient or not getattr(recipient, "id", None):
            continue
        if recipient.id == exclude_id:
            continue
        if recipient.id in seen_ids:
            continue
        unique_recipients.append(recipient)
        seen_ids.add(recipient.id)

    return unique_recipients


def build_bitacora_entry_message(entry):
    case_obj = entry.case
    author_name = getattr(entry.author, "full_name", None) or "Un usuario"
    event_label = entry.get_event_type_display()
    created_text = timezone.localtime(entry.created_at).strftime("%d/%m/%Y %I:%M %p")
    scheduled_text = ""
    term_text = ""

    if entry.scheduled_for:
        scheduled_text = (
            f" Evento programado para "
            f"{timezone.localtime(entry.scheduled_for).strftime('%d/%m/%Y %I:%M %p')}."
        )

    if entry.starts_new_term and entry.term_due_at:
        term_text = (
            f" Nuevo término con vencimiento "
            f"{timezone.localtime(entry.term_due_at).strftime('%d/%m/%Y %I:%M %p')}."
        )

    return {
        "title": f"Nuevo evento en el caso {case_obj.case_number}",
        "message": (
            f"{author_name} registró '{event_label}' en la bitácora del caso "
            f"{case_obj.case_number} el {created_text}. {entry.content}"
            f"{scheduled_text}{term_text}"
        ),
    }


def notify_case_participants_bitacora_entry(entry, send_email=False, email_recipients=None):
    """
    Crea notificaciones internas para los participantes del caso (estudiante, asesor, secretaria).
    Si send_email=True, envía correo a las direcciones presentes en email_recipients (set de strings).
    Si email_recipients es None, envía a todos los participantes con email (excepto el autor).
    El beneficiario nunca recibe notificación interna, pero sí puede recibir correo si está en
    email_recipients y el evento es Reunión, Audiencia o Cita de tribunal.
    """
    data = build_bitacora_entry_message(entry)
    recipients = get_case_participants(entry.case, exclude_user=entry.author)
    notifications = []

    BENEFICIARIO_EVENT_TYPES = {
        BitacoraEntry.EventType.REUNION,
        BitacoraEntry.EventType.AUDIENCIA,
        BitacoraEntry.EventType.TRIBUNAL,
    }

    # Notificaciones internas + correo para estudiante, asesor y secretaria
    for recipient in recipients:
        notification, _ = Notification.objects.get_or_create(
            recipient=recipient,
            case=entry.case,
            related_entry=entry,
            notification_type=Notification.NotificationType.INFO,
            defaults={
                "title": data["title"],
                "message": data["message"],
            },
        )
        notifications.append(notification)

        if not send_email:
            continue
        email = getattr(recipient, "email", None)
        if not email:
            continue
        if email_recipients is not None and email not in email_recipients:
            continue
        _send_bitacora_email(data, email, entry)

    # Correo al beneficiario (sin notificación interna)
    # Solo en eventos de Reunión, Audiencia o Tribunal
    if send_email:
        beneficiary = getattr(entry.case, "beneficiary", None)
        if beneficiary:
            email = getattr(beneficiary, "email", None)
            if email and (email_recipients is None or email in email_recipients):
                if entry.event_type in BENEFICIARIO_EVENT_TYPES:
                    _send_bitacora_email(data, email, entry)

    return notifications


def _send_bitacora_email(data, recipient_email, entry):
    """Envía el correo de notificación de bitácora con formato HTML."""
    from django.utils import timezone as tz

    case = entry.case
    author_name = getattr(entry.author, "full_name", None) or "Un usuario"
    event_label = entry.get_event_type_display() if hasattr(entry, "get_event_type_display") else ""

    scheduled_row = ""
    if entry.scheduled_for:
        fecha = tz.localtime(entry.scheduled_for).strftime("%d/%m/%Y %I:%M %p")
        scheduled_row = f"<p style='margin:0 0 6px;font-size:14px;color:#374151;'><strong>Fecha programada:</strong> {fecha}</p>"

    html_message = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f5;padding:40px 16px;">
  <div style="max-width:520px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <div style="background:#7c6fd9;padding:28px 32px;text-align:center;">
      <h1 style="color:white;margin:0;font-size:22px;font-weight:700;">Consultorio Jurídico</h1>
    </div>

    <div style="padding:32px;">
      <h2 style="color:#1a1a1a;font-size:20px;margin:0 0 12px;">Nueva entrada en Bitácora</h2>
      <p style="color:#555;line-height:1.6;margin:0 0 20px;">Se ha registrado una nueva entrada en el caso <strong>{case.case_number}</strong> en el que participas.</p>

      <div style="background:#f9fafb;border-left:3px solid #7c6fd9;border-radius:4px;padding:14px 16px;margin-bottom:20px;">
        <p style="margin:0 0 6px;font-size:14px;color:#374151;"><strong>Caso:</strong> {case.case_number}</p>
        <p style="margin:0 0 6px;font-size:14px;color:#374151;"><strong>Registrado por:</strong> {author_name}</p>
        {"<p style='margin:0 0 6px;font-size:14px;color:#374151;'><strong>Tipo de evento:</strong> " + event_label + "</p>" if event_label else ""}
        {scheduled_row}
      </div>

      <p style="color:#374151;font-size:14px;font-weight:700;margin:0 0 6px;">Motivo:</p>
      <p style="color:#555;font-size:14px;line-height:1.6;margin:0;">{entry.content}</p>
    </div>

    <div style="background:#f9fafb;padding:16px 32px;text-align:center;border-top:1px solid #e5e7eb;">
      <p style="color:#9ca3af;font-size:12px;margin:0;">© Consultorio Jurídico — Universidad Icesi</p>
    </div>

  </div>
</body>
</html>"""

    max_intentos = 3
    for intento in range(1, max_intentos + 1):
        try:
            send_mail(
                subject=data["title"],
                message=data["message"],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info("Correo de bitácora enviado a %s (caso %s)", recipient_email, case.case_number)
            return
        except Exception as exc:
            logger.warning("Intento %d/%d fallido al enviar correo a %s: %s", intento, max_intentos, recipient_email, exc)
    logger.error("No se pudo enviar el correo de bitácora a %s después de %d intentos (caso %s)", recipient_email, max_intentos, case.case_number)
