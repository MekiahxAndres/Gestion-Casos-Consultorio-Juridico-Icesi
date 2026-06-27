import json
import logging
from dataclasses import dataclass
from urllib import parse, request

from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


@dataclass
class TeamsMeetingResult:
    created: bool = False
    join_url: str = ""
    web_url: str = ""
    error: str = ""


def _graph_config():
    tenant_id = getattr(settings, "MICROSOFT_GRAPH_TENANT_ID", "")
    client_id = getattr(settings, "MICROSOFT_GRAPH_CLIENT_ID", "")
    client_secret = getattr(settings, "MICROSOFT_GRAPH_CLIENT_SECRET", "")
    organizer = getattr(settings, "MICROSOFT_GRAPH_ORGANIZER_EMAIL", "")

    if not all([tenant_id, client_id, client_secret, organizer]):
        return None

    return {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "organizer": organizer,
    }


def _post_form(url, data):
    encoded = parse.urlencode(data).encode("utf-8")
    req = request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url, token, payload):
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def create_teams_calendar_event(*, subject, body, start_datetime, end_datetime, attendees):
    """
    Crea un evento de calendario con reunión de Teams vía Microsoft Graph.
    Si Graph no está configurado, retorna un resultado no creado sin interrumpir el flujo local.
    """
    config = _graph_config()
    if not config:
        return TeamsMeetingResult(error="Microsoft Graph no está configurado.")

    attendee_emails = sorted({email for email in attendees if email})
    try:
        token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
        token_data = _post_form(
            token_url,
            {
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            },
        )
        token = token_data["access_token"]

        tz_name = getattr(settings, "TIME_ZONE", "America/Bogota")
        payload = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "start": {
                "dateTime": timezone.localtime(start_datetime).strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": tz_name,
            },
            "end": {
                "dateTime": timezone.localtime(end_datetime).strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": tz_name,
            },
            "attendees": [
                {
                    "emailAddress": {"address": email},
                    "type": "required",
                }
                for email in attendee_emails
            ],
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness",
        }
        organizer = parse.quote(config["organizer"])
        event_url = f"https://graph.microsoft.com/v1.0/users/{organizer}/events"
        event = _post_json(event_url, token, payload)
        join_url = (event.get("onlineMeeting") or {}).get("joinUrl", "")
        return TeamsMeetingResult(
            created=bool(join_url),
            join_url=join_url,
            web_url=event.get("webLink", ""),
        )
    except Exception as exc:
        logger.exception("No se pudo crear la reunión de Teams por Microsoft Graph")
        return TeamsMeetingResult(error=str(exc))
