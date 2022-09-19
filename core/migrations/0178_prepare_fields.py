import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0177_restrict_placement_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidatesplitallocation',
            name='placement',
            field=models.IntegerField(),
        ),
    ]
