import logging
import time

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from tculink.sms import BaseSMSProvider

logger = logging.getLogger(__name__)


class ProviderSmsApi(BaseSMSProvider):
    CONFIGURATION_FIELDS = [
        ('to', _("Destination phone number")),
    ]
    HELP_TEXT = _("Uses the internal SMS API service. Accepted formats: 0XXXXXXXXX or +33XXXXXXXXX.")

    def send(self, message, configuration):
        if "to" not in configuration:
            raise Exception("Configuration is incomplete")

        payload = {
            "to": configuration["to"],
            "message": message,
        }
        endpoint = f"{settings.SMSAPI_BASE_URL.rstrip('/')}/sms/send"
        timeout = settings.SMSAPI_TIMEOUT

        last_response = None
        last_error = None
        for attempt in range(3):
            try:
                response = requests.post(
                    endpoint,
                    json=payload,
                    timeout=timeout,
                    headers={
                        "User-Agent": "OpenCarWings/1.0",
                        "Content-Type": "application/json",
                    },
                )
                last_response = response

                if response.status_code == 200:
                    body = response.json()
                    logger.info(
                        "smsapi send success request_id=%s provider=%s to=%s",
                        body.get("request_id"),
                        body.get("provider"),
                        configuration["to"],
                    )
                    return True

                if response.status_code < 500:
                    body = {}
                    try:
                        body = response.json()
                    except ValueError:
                        body = {"raw": response.text}
                    logger.warning(
                        "smsapi send rejected status=%s to=%s body=%s",
                        response.status_code,
                        configuration["to"],
                        body,
                    )
                    return False

                last_error = f"HTTP {response.status_code}"
            except requests.RequestException as exc:
                last_error = str(exc)

            if attempt < 2:
                time.sleep(min(2 ** attempt, 10))

        body = {}
        if last_response is not None:
            try:
                body = last_response.json()
            except ValueError:
                body = {"raw": last_response.text}
            logger.error(
                "smsapi send failed status=%s to=%s error=%s body=%s",
                last_response.status_code,
                configuration["to"],
                last_error,
                body,
            )
        else:
            logger.error(
                "smsapi send failed without response to=%s error=%s",
                configuration["to"],
                last_error,
            )
        return False
