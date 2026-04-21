import logging

import requests
from django.utils.translation import gettext_lazy as _

from tculink.sms import BaseSMSProvider

logger = logging.getLogger(__name__)


class ProviderFreeMobile(BaseSMSProvider):
    CONFIGURATION_FIELDS = [
        ("mobile_number", _("Destination phone number")),
        ("free_user", _("Free Mobile user ID")),
        ("free_api_key", _("Free Mobile API key")),
    ]
    HELP_TEXT = _("Enable SMS notifications in your Free Mobile account and copy your API key from the account options page.")
    LINK = "https://mobile.free.fr/account/mes-options"

    def send(self, message, configuration):
        required_fields = ("free_user", "free_api_key")
        if not all(configuration.get(field) for field in required_fields):
            raise Exception("Configuration is incomplete")

        response = requests.get(
            "https://smsapi.free-mobile.fr/sendmsg",
            params={
                "user": configuration["free_user"],
                "pass": configuration["free_api_key"],
                "msg": message,
            },
            timeout=10,
            headers={"User-Agent": "OpenCarWings/1.0"},
        )
        if response.status_code == 200:
            return True

        logger.warning(
            "freemobile send rejected status=%s body=%s",
            response.status_code,
            response.text,
        )
        return False
