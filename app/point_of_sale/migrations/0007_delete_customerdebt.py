# Generated by Django 4.2.9 on 2025-07-03 22:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('point_of_sale', '0006_remove_salesorder_customer_name_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CustomerDebt',
        ),
    ]
