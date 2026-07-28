from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0018_student_is_paid_student_payment_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='payment_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='student',
            name='razorpay_signature',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='student',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
