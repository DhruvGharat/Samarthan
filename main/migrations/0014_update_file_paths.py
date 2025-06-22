from django.db import migrations

def update_file_paths(apps, schema_editor):
    NGO = apps.get_model('main', 'NGO')
    SignupNGO = apps.get_model('main', 'SignupNGO')
    
    # Update NGO model paths
    for ngo in NGO.objects.all():
        if ngo.ngo_profile_image and 'ngo_documents' in ngo.ngo_profile_image.name:
            new_name = ngo.ngo_profile_image.name.replace('ngo_documents', 'ngo/profile/images')
            ngo.ngo_profile_image.name = new_name
        if ngo.ngo_certificate and 'ngo_documents' in ngo.ngo_certificate.name:
            new_name = ngo.ngo_certificate.name.replace('ngo_documents', 'ngo/certificates')
            ngo.ngo_certificate.name = new_name
        ngo.save()
    
    # Update SignupNGO model paths
    for signup in SignupNGO.objects.all():
        if signup.ngo_profile_image and 'ngo_documents' in signup.ngo_profile_image.name:
            new_name = signup.ngo_profile_image.name.replace('ngo_documents', 'ngo/profile/images')
            signup.ngo_profile_image.name = new_name
        if signup.ngo_certificate and 'ngo_documents' in signup.ngo_certificate.name:
            new_name = signup.ngo_certificate.name.replace('ngo_documents', 'ngo/certificates')
            signup.ngo_certificate.name = new_name
        signup.save()

def reverse_file_paths(apps, schema_editor):
    NGO = apps.get_model('main', 'NGO')
    SignupNGO = apps.get_model('main', 'SignupNGO')
    
    # Reverse NGO model paths
    for ngo in NGO.objects.all():
        if ngo.ngo_profile_image and 'ngo/profile/images' in ngo.ngo_profile_image.name:
            new_name = ngo.ngo_profile_image.name.replace('ngo/profile/images', 'ngo_documents')
            ngo.ngo_profile_image.name = new_name
        if ngo.ngo_certificate and 'ngo/certificates' in ngo.ngo_certificate.name:
            new_name = ngo.ngo_certificate.name.replace('ngo/certificates', 'ngo_documents')
            ngo.ngo_certificate.name = new_name
        ngo.save()
    
    # Reverse SignupNGO model paths
    for signup in SignupNGO.objects.all():
        if signup.ngo_profile_image and 'ngo/profile/images' in signup.ngo_profile_image.name:
            new_name = signup.ngo_profile_image.name.replace('ngo/profile/images', 'ngo_documents')
            signup.ngo_profile_image.name = new_name
        if signup.ngo_certificate and 'ngo/certificates' in signup.ngo_certificate.name:
            new_name = signup.ngo_certificate.name.replace('ngo/certificates', 'ngo_documents')
            signup.ngo_certificate.name = new_name
        signup.save()

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0013_alter_expense_bill_photo_alter_ngo_ngo_certificate_and_more'),
    ]

    operations = [
        migrations.RunPython(update_file_paths, reverse_file_paths),
    ]
