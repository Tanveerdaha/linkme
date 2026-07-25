# Generated for Voice/Link message types + metadata

import django.core.validators
from django.db import migrations, models

import apps.messaging.models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0001_phase6_messaging"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="message",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.messaging.models.message_attachment_upload_to,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=[
                            "doc",
                            "docx",
                            "jpg",
                            "jpeg",
                            "m4a",
                            "mov",
                            "mp3",
                            "mp4",
                            "ogg",
                            "pdf",
                            "png",
                            "webm",
                            "webp",
                        ]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="message",
            name="message_type",
            field=models.CharField(
                choices=[
                    ("TEXT", "Text"),
                    ("IMAGE", "Image"),
                    ("VIDEO", "Video"),
                    ("FILE", "File"),
                    ("VOICE", "Voice"),
                    ("LINK", "Link"),
                ],
                db_index=True,
                default="TEXT",
                max_length=16,
            ),
        ),
    ]
