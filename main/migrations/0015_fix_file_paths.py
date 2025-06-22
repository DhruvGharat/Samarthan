from django.db import migrations
import os
from django.core.files import File

def fix_file_paths(apps, schema_editor):
    NGO = apps.get_model('main', 'NGO')
    SignupNGO = apps.get_model('main', 'SignupNGO')
    
    def fix_ngo_paths(ngo):
        # Fix profile image path
        if ngo.ngo_profile_image:
            old_path = ngo.ngo_profile_image.path
            if os.path.exists(old_path):
                new_name = f"ngo/profile/images/{os.path.basename(old_path)}"
                new_path = os.path.join('media', new_name)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                if os.path.exists(old_path):
                    with open(old_path, 'rb') as f:
                        ngo.ngo_profile_image.save(new_name, File(f), save=False)
        
        # Fix certificate path
        if ngo.ngo_certificate:
            old_path = ngo.ngo_certificate.path
            if os.path.exists(old_path):
                new_name = f"ngo/certificates/{os.path.basename(old_path)}"
                new_path = os.path.join('media', new_name)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                if os.path.exists(old_path):
                    with open(old_path, 'rb') as f:
                        ngo.ngo_certificate.save(new_name, File(f), save=False)
        
        ngo.save()
    
    # Update NGO model paths
    for ngo in NGO.objects.all():
        fix_ngo_paths(ngo)
    
    # Update SignupNGO model paths
    for signup in SignupNGO.objects.all():
        fix_ngo_paths(signup)

def reverse_file_paths(apps, schema_editor):
    pass  # We don't want to reverse this migration

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0014_update_file_paths'),
    ]

    operations = [
        migrations.RunPython(fix_file_paths, reverse_file_paths),
    ]
