# Generated by Django 5.0.7 on 2024-08-06 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airport", "0006_alter_airplane_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="airplanetype",
            name="manufacturer",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
