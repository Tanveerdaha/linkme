from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_google_oauth"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                blank=True,
                db_index=True,
                max_length=254,
                null=True,
                unique=True,
                verbose_name="email address",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="E.164 format, e.g. +923001234567",
                max_length=20,
                null=True,
                unique=True,
                verbose_name="phone number",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="auth_provider",
            field=models.CharField(
                choices=[
                    ("email", "Email"),
                    ("google", "Google"),
                    ("phone", "Phone"),
                ],
                db_index=True,
                default="email",
                max_length=20,
            ),
        ),
    ]
