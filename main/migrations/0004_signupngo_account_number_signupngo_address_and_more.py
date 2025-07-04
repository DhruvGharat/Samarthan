# Generated by Django 5.1.6 on 2025-03-16 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rename_date_expense_transaction_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='signupngo',
            name='account_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='signupngo',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='signupngo',
            name='bank_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='signupngo',
            name='contact_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='signupngo',
            name='documents',
            field=models.FileField(blank=True, null=True, upload_to='ngo_documents/'),
        ),
        migrations.AddField(
            model_name='signupngo',
            name='ifsc_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='signupngo',
            name='mission',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='signupngo',
            name='category',
            field=models.CharField(choices=[('education', 'Education'), ('healthcare', 'Healthcare'), ('clothing', 'Clothing'), ('food', 'Food'), ('shelter', 'Shelter'), ('animal', 'Animal Welfare')], max_length=20),
        ),
    ]
