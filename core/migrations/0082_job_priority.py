# Generated by Django 2.2.2 on 2019-06-24 01:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0081_client_zoho_auth_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='priority',
            field=models.BooleanField(default=False),
        ),
    ]