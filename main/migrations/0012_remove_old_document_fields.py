from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_migrate_document_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signupngo',
            name='documents',
        ),
        migrations.RemoveField(
            model_name='signupngo',
            name='additional_certificate',
        ),
        migrations.RemoveField(
            model_name='ngo',
            name='registration_certificate',
        ),
    ]
