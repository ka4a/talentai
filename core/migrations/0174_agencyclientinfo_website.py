# Generated by Django 2.2.11 on 2020-04-22 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0173_notification_draft'),
    ]

    operations = [
        migrations.AddField(
            model_name='agencyclientinfo',
            name='website',
            field=models.URLField(blank=True, default=''),
        ),
    ]