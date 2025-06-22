from django.contrib import admin
from .models import SignupUser, SignupNGO, NGO, Donation, Expense, Volunteer, PreRegisteredNGO

@admin.register(SignupUser)
class SignupUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('first_name',)

@admin.register(SignupNGO)
class SignupNGOAdmin(admin.ModelAdmin):
    list_display = ('ngo_name', 'registration_number', 'category', 'email')
    search_fields = ('ngo_name', 'registration_number', 'email')
    list_filter = ('category',)
    ordering = ('ngo_name',)

@admin.register(NGO)
class NGOAdmin(admin.ModelAdmin):
    list_display = ('name', 'services', 'contact_number', 'email', 'is_verified')
    list_filter = ('services', 'is_verified')
    search_fields = ('name', 'email', 'registration_number')
    list_per_page = 20

    def category_display(self, obj):
        return obj.signup_ngo.category if obj.signup_ngo else "N/A"
    category_display.short_description = 'Category'

from django.contrib import admin
from main.models import Donation
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'ngo', 'amount', 'donated_at', 'receipt_number')
    list_filter = ('ngo', 'donated_at')
    search_fields = ('user__username', 'ngo__name', 'receipt_number')
    readonly_fields = ('receipt_number', 'receipt_generated_at')

from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('ngo', 'transaction_date', 'description', 'amount', 'created_at')
    search_fields = ('ngo__name', 'description')
    list_filter = ('transaction_date', 'created_at')
    ordering = ('-transaction_date', '-created_at')

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('name', 'ngo', 'contact', 'preferred_time', 'status')
    list_filter = ('status', 'preferred_time', 'ngo')
    search_fields = ('name', 'contact', 'ngo__name')
    readonly_fields = ('created_at',)

@admin.register(PreRegisteredNGO)
class DummyData(admin.ModelAdmin):
    list_display = ('ngo_name', 'registration_number', 'category')
    search_fields = ('ngo__name', 'registration_number')
   