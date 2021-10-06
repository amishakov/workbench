# Generated by Django 3.2.7 on 2021-10-06 13:20

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0019_auto_20200523_0929"),
        ("invoices", "0022_recurringinvoice_create_project"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectedInvoice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("invoiced_on", models.DateField(verbose_name="invoiced on")),
                (
                    "gross_margin",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="gross margin",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="description"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projected_invoices",
                        to="projects.project",
                        verbose_name="project",
                    ),
                ),
            ],
            options={
                "ordering": ["invoiced_on"],
                "verbose_name": "projected invoice",
                "verbose_name_plural": "projected invoices",
            },
        ),
    ]
