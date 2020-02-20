# Generated by Django 3.0.3 on 2020-02-19 13:52

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contacts", "0012_person_date_of_birth"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Attribute",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="position"),
                ),
                (
                    "is_archived",
                    models.BooleanField(default=False, verbose_name="is archived"),
                ),
            ],
            options={
                "verbose_name": "attribute",
                "verbose_name_plural": "attributes",
                "ordering": ("position", "id"),
            },
        ),
        migrations.CreateModel(
            name="AttributeGroup",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="position"),
                ),
                (
                    "is_archived",
                    models.BooleanField(default=False, verbose_name="is archived"),
                ),
                (
                    "is_required",
                    models.BooleanField(default=True, verbose_name="is required"),
                ),
            ],
            options={
                "verbose_name": "attribute group",
                "verbose_name_plural": "attribute groups",
                "ordering": ("position", "id"),
            },
        ),
        migrations.CreateModel(
            name="ClosingType",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "represents_a_win",
                    models.BooleanField(default=False, verbose_name="represents a win"),
                ),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="position"),
                ),
            ],
            options={
                "verbose_name": "closing type",
                "verbose_name_plural": "closing types",
                "ordering": ("position", "id"),
            },
        ),
        migrations.CreateModel(
            name="Deal",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="value",
                    ),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        choices=[(10, "open"), (20, "accepted"), (30, "declined")],
                        default=10,
                        verbose_name="status",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="created at"
                    ),
                ),
                (
                    "closed_on",
                    models.DateField(blank=True, null=True, verbose_name="closed on"),
                ),
                (
                    "closing_notice",
                    models.TextField(blank=True, verbose_name="closing notice"),
                ),
                ("_fts", models.TextField(blank=True, editable=False)),
            ],
            options={
                "verbose_name": "deal",
                "verbose_name_plural": "deals",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="Stage",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="position"),
                ),
            ],
            options={
                "verbose_name": "stage",
                "verbose_name_plural": "stages",
                "ordering": ("position", "id"),
            },
        ),
        migrations.CreateModel(
            name="ValueType",
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
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="position"),
                ),
            ],
            options={
                "verbose_name": "value type",
                "verbose_name_plural": "value types",
                "ordering": ("position", "id"),
            },
        ),
        migrations.CreateModel(
            name="DealAttribute",
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
                (
                    "attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="deals.Attribute",
                        verbose_name="attribute",
                    ),
                ),
                (
                    "deal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="deals.Deal",
                        verbose_name="deal",
                    ),
                ),
            ],
            options={
                "verbose_name": "deal attribute",
                "verbose_name_plural": "deal attributes",
            },
        ),
        migrations.AddField(
            model_name="deal",
            name="attributes",
            field=models.ManyToManyField(
                through="deals.DealAttribute",
                to="deals.Attribute",
                verbose_name="attributes",
            ),
        ),
        migrations.AddField(
            model_name="deal",
            name="closing_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="deals.ClosingType",
                verbose_name="closing type",
            ),
        ),
        migrations.AddField(
            model_name="deal",
            name="contact",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="contacts.Person",
                verbose_name="contact",
            ),
        ),
        migrations.AddField(
            model_name="deal",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="contacts.Organization",
                verbose_name="customer",
            ),
        ),
        migrations.AddField(
            model_name="deal",
            name="owned_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="responsible",
            ),
        ),
        migrations.AddField(
            model_name="deal",
            name="stage",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="deals",
                to="deals.Stage",
                verbose_name="stage",
            ),
        ),
        migrations.AddField(
            model_name="attribute",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributes",
                to="deals.AttributeGroup",
                verbose_name="attribute group",
            ),
        ),
        migrations.CreateModel(
            name="Value",
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
                (
                    "value",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="value",
                    ),
                ),
                (
                    "deal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="values",
                        to="deals.Deal",
                        verbose_name="deal",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="deals.ValueType",
                        verbose_name="type",
                    ),
                ),
            ],
            options={
                "verbose_name": "value",
                "verbose_name_plural": "values",
                "ordering": ["type"],
                "unique_together": {("deal", "type")},
            },
        ),
    ]
