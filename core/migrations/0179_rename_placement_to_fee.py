import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0178_prepare_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candidatesplitallocation', old_name='placement', new_name='fee',
        ),
        migrations.RenameModel('CandidatePlacement', 'Fee'),
        migrations.RenameModel('CandidateSplitAllocation', 'FeeSplitAllocation'),
    ]
