# Generated by Django 4.1.13 on 2025-01-24 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weedGuardApp', '0008_alter_prediction_timestamp'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Your Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Your Email')),
                ('message', models.TextField(verbose_name='Your Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Contact Message',
                'verbose_name_plural': 'Contact Messages',
            },
        ),
    ]
