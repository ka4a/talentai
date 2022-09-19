# Generated by Django 2.1.2 on 2018-10-12 19:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_agency'),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('resume', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='candidate',
            name='agency',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Agency'),
        ),
    ]