from unittest.mock import patch

from django.test import TestCase, override_settings

from db.models import Car, CarSMSCredential, EVInfo, LocationInfo, TCUConfiguration, User


@override_settings(SECRET_KEY="unit-test-secret-key-for-sms-crypto-tests")
class CommandApiFreeMobileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="password", tcu_pass_hash="HASHED")
        self.car = Car.objects.create(
            vin="SJNFAAZE0U0000002",
            nickname="Leaf 2",
            sms_provider="freemobile",
            sms_config={"provider": "freemobile"},
            tcu_configuration=TCUConfiguration.objects.create(),
            location=LocationInfo.objects.create(),
            ev_info=EVInfo.objects.create(),
            owner=self.user,
        )
        self.client.force_login(self.user)

    @patch("api.views.send_using_provider")
    def test_command_api_uses_runtime_sms_configuration(self, mocked_send):
        credential = CarSMSCredential(car=self.car, provider="freemobile")
        credential.set_free_mobile_credentials("+33123456789", "12345678", "my-api-key")
        credential.save()
        mocked_send.return_value = True

        response = self.client.post(
            f"/api/command/{self.car.vin}/",
            data={"command_type": 1},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        _, sent_configuration = mocked_send.call_args[0]
        self.assertEqual(sent_configuration["provider"], "freemobile")
        self.assertEqual(sent_configuration["free_user"], "12345678")
        self.assertEqual(sent_configuration["free_api_key"], "my-api-key")

    def test_command_api_returns_500_when_credentials_missing(self):
        response = self.client.post(
            f"/api/command/{self.car.vin}/",
            data={"command_type": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)
