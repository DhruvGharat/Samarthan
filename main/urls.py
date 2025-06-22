from django.urls import path
from . import views
from .views import donate_to_ngo
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('ngo-discovery/', views.ngo_discovery, name='ngo_discovery'),
    path('ngo/details/<int:ngo_id>/', views.ngo_details, name='ngo_details'),
    path('donation-tracking/', views.donation_tracking, name='donation_tracking'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/user/', views.login_user, name='login_user'),
    path('login/ngo/', views.login_ngo, name='login_ngo'),
    path('signup/user/', views.signup_user, name='signup_user'),
    path('signup/ngo/', views.signup_ngo, name='signup_ngo'),
    path('base/ngo/', views.ngo_base, name='ngo_base'),
    path('logout/', views.logout_user, name='logout'),

    
    # New NGO dashboard URLs
    path('ngo/profile/<int:ngo_id>/', views.ngo_profile, name='ngo_profile'),
    path('ngo/profile/', views.ngo_profile, name='ngo_profile_self'),  # For viewing own profile
    path('ngo/donations/', views.ngo_donations, name='ngo_donations'),
    path('ngo/add-expense/', views.add_expense, name='add_expense'),
    path('ngo/about/', views.ngo_about, name='ngo_about'),
    path('ngo/contact/', views.ngo_contact, name='ngo_contact'),
    path('ngo/volunteer/', views.ngo_volunteer, name='ngo_volunteer'),
    path('ngo/volunteer/update/<int:volunteer_id>/', views.update_volunteer_status, name='update_volunteer_status'),

    path('donate/<int:ngo_id>/', donate_to_ngo, name='donate_to_ngo'),

    path('api/receipt/<str:receipt_number>/', views.get_receipt, name='get_receipt'),
    path('get_receipt/<int:donation_id>/', views.get_receipt, name='get_receipt'),
    path('register_volunteer/', views.register_volunteer, name='register_volunteer'),
    path('volunteer/', views.volunteer_registration, name='volunteer_registration'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),

    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_user_info, name='admin_user_info'),
    path('admin/users/remove/<int:user_id>/', views.admin_remove_user, name='admin_remove_user'),
    path('admin/ngos/', views.admin_ngo_info, name='admin_ngo_info'),
    path('admin/ngos/verify/<int:ngo_id>/', views.admin_verify_ngo, name='admin_verify_ngo'),
    path('admin/ngos/remove/<int:ngo_id>/', views.admin_remove_ngo, name='admin_remove_ngo'),
    path('admin/ngo/<int:ngo_id>/', views.admin_ngo_details, name='admin_ngo_details'),
    path('admin/donations/', views.admin_donations, name='admin_donations'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)