# Generated by Django 2.2.11 on 2020-03-25 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0160_skilldomain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='source',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
