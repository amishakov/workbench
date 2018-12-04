# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-24 07:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from workbench.tools.search import migration_sql


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailAddress",
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
                ("type", models.CharField(max_length=40, verbose_name="type")),
                (
                    "weight",
                    models.SmallIntegerField(
                        default=0, editable=False, verbose_name="weight"
                    ),
                ),
                ("email", models.EmailField(max_length=254, verbose_name="email")),
            ],
            options={
                "verbose_name_plural": "email addresses",
                "verbose_name": "email address",
                "ordering": ("-weight", "id"),
            },
        ),
        migrations.CreateModel(
            name="Group",
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
                ("title", models.CharField(max_length=100, verbose_name="title")),
            ],
            options={
                "verbose_name_plural": "groups",
                "verbose_name": "group",
                "ordering": ("title",),
            },
        ),
        migrations.CreateModel(
            name="Organization",
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
                ("name", models.TextField(verbose_name="name")),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        related_name="_organization_groups_+",
                        to="contacts.Group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "primary_contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="primary contact",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "organizations",
                "verbose_name": "organization",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Person",
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
                    "full_name",
                    models.CharField(max_length=100, verbose_name="full name"),
                ),
                (
                    "address",
                    models.CharField(
                        blank=True,
                        help_text="E.g. Dear John.",
                        max_length=100,
                        verbose_name="address",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        related_name="_person_groups_+",
                        to="contacts.Group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="people",
                        to="contacts.Organization",
                        verbose_name="organization",
                    ),
                ),
                (
                    "primary_contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="primary contact",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "people",
                "verbose_name": "person",
                "ordering": ("full_name",),
            },
        ),
        migrations.CreateModel(
            name="PhoneNumber",
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
                ("type", models.CharField(max_length=40, verbose_name="type")),
                (
                    "weight",
                    models.SmallIntegerField(
                        default=0, editable=False, verbose_name="weight"
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(max_length=100, verbose_name="phone number"),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="phonenumbers",
                        to="contacts.Person",
                        verbose_name="person",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "phone numbers",
                "verbose_name": "phone number",
                "ordering": ("-weight", "id"),
            },
        ),
        migrations.CreateModel(
            name="PostalAddress",
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
                ("type", models.CharField(max_length=40, verbose_name="type")),
                (
                    "weight",
                    models.SmallIntegerField(
                        default=0, editable=False, verbose_name="weight"
                    ),
                ),
                ("postal_address", models.TextField(verbose_name="postal address")),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="postaladdresses",
                        to="contacts.Person",
                        verbose_name="person",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "postal addresses",
                "verbose_name": "postal address",
                "ordering": ("-weight", "id"),
            },
        ),
        migrations.AddField(
            model_name="emailaddress",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="emailaddresses",
                to="contacts.Person",
                verbose_name="person",
            ),
        ),
        migrations.RunSQL(
            "SELECT audit_audit_table('contacts_organization');"
            "SELECT audit_audit_table('contacts_person');"
            "SELECT audit_audit_table('contacts_phonenumber');"
            "SELECT audit_audit_table('contacts_emailaddress');"
            "SELECT audit_audit_table('contacts_postaladdress');",
            "",
        ),
        migrations.RunSQL(*migration_sql("contacts_organization", "name")),
        migrations.RunSQL(
            *migration_sql("contacts_person", "full_name, address, notes")
        ),
    ]
