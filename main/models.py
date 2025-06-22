from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

# Choices for NGO categories
NGO_SERVICE_CHOICES = [
    ('education', 'Education'),
    ('healthcare', 'Healthcare'),
    ('environment', 'Environment'),
    ('animal', 'Animal Welfare'),
    ('food', 'Food'),
    ('shelter', 'Shelter'),
    ('others', 'Others'),
]

# New model to store pre-registered NGOs
class PreRegisteredNGO(models.Model):
    ngo_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=NGO_SERVICE_CHOICES)

    def __str__(self):
        return self.ngo_name

# Existing model for NGOs signing up
class SignupNGO(models.Model):
    ngo_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=NGO_SERVICE_CHOICES)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed password
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    mission = models.TextField(null=True, blank=True)

    # Document Upload
    ngo_profile_image = models.FileField(upload_to='ngo/profile/images/', null=True, blank=True, verbose_name='NGO Profile Image')
    ngo_certificate = models.FileField(upload_to='ngo/certificates/', null=True, blank=True, verbose_name='NGO Certificate')

    # Bank Details
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.ngo_name



class SignupUser(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed password

    def __str__(self):
        return self.first_name




class NGO(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    signup_ngo = models.ForeignKey(SignupNGO, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    services = models.CharField(max_length=255, choices=NGO_SERVICE_CHOICES, null=True, blank=True)
    mission = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Bank Details
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Verification Details
    registration_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    ngo_profile_image = models.FileField(upload_to='ngo/profile/images/', null=True, blank=True, verbose_name='NGO Profile Image')
    ngo_certificate = models.FileField(upload_to='ngo/certificates/', null=True, blank=True, verbose_name='NGO Certificate')
    is_verified = models.BooleanField(default=False)
    
    # Social Media Links (Optional)
    website = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    other_social = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'NGO'
        verbose_name_plural = 'NGOs'


    
from django.db import models
from django.utils.timezone import now

class Donation(models.Model):
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None)  # Allow null and default
    user_account_number = models.CharField(max_length=20, null=True, blank=True)
    user_ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    user_bank_name = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donated_at = models.DateTimeField(default=now)  # Set default time
    receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Unique receipt number
    receipt_generated_at = models.DateTimeField(default=now)  # When the receipt was generated

    def __str__(self):
        user_name = f"{self.user.first_name} {self.user.last_name}" if self.user else "Anonymous"
        ngo_name = self.ngo.name if self.ngo else "Unknown NGO"
        return f"Donation by {user_name} to {ngo_name} - ₹{self.amount}"

    def generate_receipt_number(self):
        """Generate a unique receipt number for the donation"""
        if not self.receipt_number:
            # Format: SAMR-YYYYMMDD-XXXXXX where X is a random number
            from datetime import datetime
            import random
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            self.receipt_number = f"SAMR-{date_str}-{random_str}"
        return self.receipt_number




from django.db import models

class Expense(models.Model):
    ngo = models.ForeignKey('NGO', on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateField()
    description = models.TextField()
    bill_photo = models.ImageField(upload_to='expense/bills/', blank=True, null=True)
    created_at = models.DateTimeField(default=now)  # Instead of auto_now_add=True

    def __str__(self):
        return f"{self.ngo} | {self.description} - ₹{self.amount} ({self.transaction_date})"

class Volunteer(models.Model):
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    preferred_days = models.JSONField()  # Will store list of selected days
    preferred_time = models.CharField(max_length=20, choices=[
        ('morning', 'Morning (9 AM - 12 PM)'),
        ('afternoon', 'Afternoon (12 PM - 4 PM)'),
        ('evening', 'Evening (4 PM - 7 PM)')
    ])
    ngo = models.ForeignKey('NGO', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')

    def __str__(self):
        return f"{self.name} - {self.ngo.name}"
