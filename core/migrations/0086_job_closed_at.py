# Generated by Django 2.2.2 on 2019-07-08 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0085_auto_20190705_1255'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
