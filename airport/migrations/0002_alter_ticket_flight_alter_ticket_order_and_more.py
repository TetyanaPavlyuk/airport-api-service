# Generated by Django 5.0.7 on 2024-08-01 17:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airport", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticket",
            name="flight",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tickets",
                to="airport.flight",
            ),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tickets",
                to="airport.order",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="crew",
            unique_together={("position", "first_name", "last_name")},
        ),
    ]
