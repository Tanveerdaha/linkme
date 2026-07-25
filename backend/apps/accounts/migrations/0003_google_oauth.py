# Generated manually for Google OAuth fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_phase8_safety_privacy"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auth_provider",
            field=models.CharField(
                choices=[("email", "Email"), ("google", "Google")],
                db_index=True,
                default="email",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="google_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
    ]
