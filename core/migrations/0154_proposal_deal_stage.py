from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0153_client_primary_contact'),
    ]
    operations = [
        migrations.AddField(
            model_name='proposalstatus',
            name='deal_stage',
            field=models.CharField(
                choices=[
                    ('first_round', 'First round'),
                    ('intermediate_round', 'Intermediate round'),
                    ('final_round', 'Final round'),
                    ('offer', 'Offer'),
                    ('out_of', 'Out of deal pipeline'),
                ],
                default='out_of',
                max_length=32,
            ),
        ),
    ]
