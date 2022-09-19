# Generated by Django 2.1.7 on 2019-03-04 21:03

import phonenumber_field.modelfields
from django.db import migrations, models

"""
has some bug with migrating phone field:
$ python manage.py sqlmigrate core 0044
add COMMIT and BEGIN:
```
UPDATE "core_candidate" SET "phone" = '' WHERE "phone" IS NULL;
COMMIT;
BEGIN;
ALTER TABLE "core_candidate" ALTER COLUMN "phone" SET NOT NULL;
```

run via psql
"""


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_candidate_phone_email_values'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candidate',
            old_name='salary_breakdon',
            new_name='salary_breakdown',
        ),
        migrations.AlterField(
            model_name='candidate',
            name='email',
            field=models.EmailField(default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='language',
            name='level',
            field=models.IntegerField(choices=[(0, 'Basic'), (1, 'Conversational'), (2, 'Business'), (3, 'Fluent'), (4, 'Native')]),
        ),
    ]
