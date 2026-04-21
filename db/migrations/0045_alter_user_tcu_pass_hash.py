from django.db import migrations, models
import re

from django.contrib.auth.hashers import Argon2PasswordHasher


LEGACY_HASH_RE = re.compile(r"^[A-F0-9]{8}$")


def migrate_legacy_tcu_hashes(apps, schema_editor):
    hasher = Argon2PasswordHasher()
    User = apps.get_model("db", "User")
    for user in User.objects.all().only("id", "tcu_pass_hash"):
        current_hash = (user.tcu_pass_hash or "").strip().upper()
        if LEGACY_HASH_RE.fullmatch(current_hash):
            user.tcu_pass_hash = hasher.encode(current_hash, hasher.salt())
            user.save(update_fields=["tcu_pass_hash"])


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0044_alter_dotfile_upload_ts_alter_routeplan_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="tcu_pass_hash",
            field=models.CharField(max_length=255),
        ),
        migrations.RunPython(migrate_legacy_tcu_hashes, migrations.RunPython.noop),
    ]
