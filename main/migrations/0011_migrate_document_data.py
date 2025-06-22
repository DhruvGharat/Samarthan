from django.db import migrations

def migrate_document_data(apps, schema_editor):
    SignupNGO = apps.get_model('main', 'SignupNGO')
    NGO = apps.get_model('main', 'NGO')

    # Migrate SignupNGO documents
    for ngo in SignupNGO.objects.all():
        if ngo.documents:
            ngo.ngo_profile_image = ngo.documents
        if ngo.additional_certificate:
            ngo.ngo_certificate = ngo.additional_certificate
        ngo.save()

    # Migrate NGO documents
    for ngo in NGO.objects.all():
        if ngo.registration_certificate:
            ngo.ngo_profile_image = ngo.registration_certificate
        ngo.save()

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_ngo_ngo_certificate_ngo_ngo_profile_image_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_document_data),
    ]
