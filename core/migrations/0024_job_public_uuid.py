# Generated by Django 2.1.2 on 2019-01-02 00:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='public_uuid',
            field=models.UUIDField(default=None, null=True, unique=True),
        ),
    ]