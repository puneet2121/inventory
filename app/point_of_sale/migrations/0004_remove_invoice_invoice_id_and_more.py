# Generated by Django 4.2.9 on 2025-02-08 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('point_of_sale', '0003_invoice_is_paid_salesorder_employee'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='invoice_id',
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Cash'), ('upi', 'UPI')], max_length=10),
        ),
    ]
