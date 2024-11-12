# Generated by Django 5.0.7 on 2024-08-05 13:12

import airport.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airport", "0005_airplane_image_alter_airplane_airplane_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="airplane",
            name="image",
            field=models.ImageField(
                null=True, upload_to=airport.models.airplane_image_path
            ),
        ),
    ]