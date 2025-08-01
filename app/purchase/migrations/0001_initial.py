# Generated by Django 4.2.9 on 2025-06-15 02:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employee', '0003_alter_employeeassignment_location_delete_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('bill_date', models.DateField()),
                ('category', models.CharField(choices=[('supplier', 'Supplier Purchase'), ('salary', 'Salary'), ('rent', 'Rent'), ('gas', 'Gas'), ('other', 'Other')], default='supplier', max_length=20)),
                ('paid_to', models.CharField(blank=True, max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='employee.employeeprofile')),
            ],
        ),
    ]
