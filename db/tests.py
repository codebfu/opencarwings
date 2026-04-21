from django.test import TestCase
from django.test import override_settings

from db.models import Car, CarSMSCredential, EVInfo, LocationInfo, TCUConfiguration, User


@override_settings(SMS_CREDENTIALS_ENCRYPTION_KEY="unit-test-secret")
class CarSMSCredentialTests(TestCase):
    def _create_car(self):
        user = User.objects.create_user(username="alice", password="password", tcu_pass_hash="HASHED")
        return Car.objects.create(
            vin="SJNFAAZE0U0000001",
            nickname="Leaf",
            sms_provider="freemobile",
            sms_config={"provider": "freemobile"},
            tcu_configuration=TCUConfiguration.objects.create(),
            location=LocationInfo.objects.create(),
            ev_info=EVInfo.objects.create(),
            owner=user,
        )

    def test_runtime_configuration_decrypts_fields(self):
        car = self._create_car()
        credential = CarSMSCredential(car=car, provider="freemobile")
        credential.set_free_mobile_credentials("+33123456789", "12345678", "my-api-key")
        credential.save()

        runtime = car.get_sms_runtime_config()
        self.assertEqual(runtime["provider"], "freemobile")
        self.assertEqual(runtime["mobile_number"], "+33123456789")
        self.assertEqual(runtime["free_user"], "12345678")
        self.assertEqual(runtime["free_api_key"], "my-api-key")

    def test_form_configuration_masks_api_key(self):
        car = self._create_car()
        credential = CarSMSCredential(car=car, provider="freemobile")
        credential.set_free_mobile_credentials("+33123456789", "12345678", "my-api-key")
        credential.save()

        form_data = car.get_sms_form_configuration()
        self.assertEqual(form_data["provider"], "freemobile")
        self.assertEqual(form_data["mobile_number"], "+33123456789")
        self.assertEqual(form_data["free_user"], "12345678")
        self.assertEqual(form_data["free_api_key"], "")
