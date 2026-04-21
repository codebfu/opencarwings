import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


def _encrypt_value(value, key_bytes):
    payload = (value or "").encode("utf-8")
    nonce = get_random_bytes(12)
    cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(payload)
    return base64.b64encode(nonce + tag + ciphertext).decode("ascii")


def migrate_sms_provider_and_credentials(apps, schema_editor):
    Car = apps.get_model("db", "Car")
    CarSMSCredential = apps.get_model("db", "CarSMSCredential")
    configured_key = getattr(settings, "SMS_CREDENTIALS_ENCRYPTION_KEY", "")
    key_bytes = hashlib.sha256(str(configured_key).encode("utf-8")).digest()

    for car in Car.objects.all().only("id", "sms_provider", "sms_config"):
        sms_config = car.sms_config if isinstance(car.sms_config, dict) else {}
        provider = sms_config.get("provider") or car.sms_provider or "manual"
        car.sms_provider = provider

        if provider == "freemobile":
            mobile_number = str(sms_config.get("mobile_number", "")).strip()
            free_user = str(sms_config.get("free_user", "")).strip()
            free_api_key = str(sms_config.get("free_api_key", "")).strip()
            if mobile_number and free_user and free_api_key:
                CarSMSCredential.objects.update_or_create(
                    car=car,
                    defaults={
                        "provider": "freemobile",
                        "mobile_number_encrypted": _encrypt_value(mobile_number, key_bytes),
                        "free_user_encrypted": _encrypt_value(free_user, key_bytes),
                        "free_api_key_encrypted": _encrypt_value(free_api_key, key_bytes),
                    },
                )
            car.sms_config = {"provider": "freemobile"}

        car.save(update_fields=["sms_provider", "sms_config"])


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0045_alter_user_tcu_pass_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="sms_provider",
            field=models.CharField(
                choices=[
                    ("smsapi", "SMS API"),
                    ("hologram", "Hologram SIM"),
                    ("monogoto", "Monogoto"),
                    ("46elks", "46elks"),
                    ("webhook", "Webhook"),
                    ("ondevice", "SMS from your device"),
                    ("smsgateway", "Use your old smartphone"),
                    ("manual", "Manual"),
                    ("freemobile", "Free Mobile"),
                ],
                default="manual",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="CarSMSCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("smsapi", "SMS API"), ("hologram", "Hologram SIM"), ("monogoto", "Monogoto"), ("46elks", "46elks"), ("webhook", "Webhook"), ("ondevice", "SMS from your device"), ("smsgateway", "Use your old smartphone"), ("manual", "Manual"), ("freemobile", "Free Mobile")], default="freemobile", max_length=32)),
                ("mobile_number_encrypted", models.TextField()),
                ("free_user_encrypted", models.TextField()),
                ("free_api_key_encrypted", models.TextField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("car", models.OneToOneField(on_delete=models.CASCADE, related_name="sms_credential", to="db.car")),
            ],
        ),
        migrations.RunPython(migrate_sms_provider_and_credentials, migrations.RunPython.noop),
    ]
