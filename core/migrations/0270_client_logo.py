# Generated by Django 3.1.10 on 2021-06-25 15:07

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0269_update_frontend_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='logo',
            field=models.ImageField(
                blank=True, null=True, upload_to=core.models.get_client_logo_file_path
            ),
        ),
    ]