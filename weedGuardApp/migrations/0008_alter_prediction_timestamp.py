# Generated by Django 4.1.13 on 2025-01-24 08:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('weedGuardApp', '0007_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prediction',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
