from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0017_school_is_tata_classedge'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='student',
            name='payment_transaction_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
