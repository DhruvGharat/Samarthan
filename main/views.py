from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import SignupUser, SignupNGO, NGO, Donation, Expense, Volunteer, NGO_SERVICE_CHOICES, PreRegisteredNGO
import json
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.utils import timezone
import logging

# Configure logging
logger = logging.getLogger(__name__)

def csrf_failure(request, reason=""):
    """Custom CSRF error view that provides more details about the failure"""
    context = {
        'reason': reason,
        'csrf_token': request.META.get('CSRF_COOKIE', 'No CSRF cookie set'),
        'request_path': request.path,
        'request_method': request.method,
        'request_headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
    }
    return render(request, 'main/csrf_error.html', context)

@login_required
def donate_to_ngo(request, ngo_id):
    ngo = get_object_or_404(NGO, id=ngo_id)

    if request.method == 'POST':
        user = request.user  # Get the logged-in user
        user_account_number = request.POST.get('user_account_number')
        user_ifsc_code = request.POST.get('user_ifsc_code')
        user_bank_name = request.POST.get('user_bank_name')
        amount = request.POST.get('amount')

        try:
            # Save the donation details
            donation = Donation.objects.create(
                ngo=ngo,
                user=user,  # Store the logged-in user
                user_account_number=user_account_number,
                user_ifsc_code=user_ifsc_code,
                user_bank_name=user_bank_name,
                amount=amount
            )

            # Generate receipt
            receipt_number = handle_donation_success(request, donation)
            
            # Add success message to session for display on redirect
            messages.success(request, f"Thank you for your donation of ₹{amount} to {ngo.name}! Your receipt number is {receipt_number}.")
            
            # Redirect to NGO discovery page instead of returning JSON
            return redirect('ngo_discovery')
            
        except Exception as e:
            messages.error(request, f"Error processing donation: {str(e)}")
            return redirect('ngo_discovery')

    return render(request, 'main/donation_form.html', {'ngo': ngo})



#********USER LOGIN AND SIGNUP***********

def login_user(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        try:
            signup_user = SignupUser.objects.get(email=email)
            
            # Check if the entered password matches the stored hashed password
            if check_password(password, signup_user.password):
                # Get or create Django User
                try:
                    user = User.objects.get(username=email)
                except User.DoesNotExist:
                    # Create a new Django User if doesn't exist
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=password,
                        first_name=signup_user.first_name,
                        last_name=signup_user.last_name
                    )

                # Authenticate and login the user
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    request.session['user_id'] = signup_user.id
                    request.session['user_name'] = signup_user.first_name
                    messages.success(request, "Login successful!")
                    return redirect('donation_tracking')
                else:
                    messages.error(request, "Authentication failed!")
            else:
                messages.error(request, "Invalid password!")
        
        except SignupUser.DoesNotExist:
            messages.error(request, "User with this email does not exist!")

    return render(request, "main/login_user.html")


def signup_user(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup_user')

        # Check if email already exists in either SignupUser or Django User
        if SignupUser.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup_user')

        # Create Django User first
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,  # create_user handles password hashing
            first_name=first_name,
            last_name=last_name
        )

        # Create SignupUser with the same hashed password
        SignupUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=django_user.password  # Use the same hashed password from Django User
        )

        messages.success(request, "User registered successfully. Please login.")
        return redirect('login_user')

    return render(request, 'main/signup_user.html')

#********USER LOGIN AND SIGNUP END END***********

#********NGO LOGIN AND SIGNUP***********

def login_ngo(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        try:
            signup_ngo = SignupNGO.objects.get(email=email)
            
            # First check if the entered password matches the stored hashed password
            if not check_password(password, signup_ngo.password):
                messages.error(request, "Invalid password!")
                return redirect('login_ngo')
                
            # Check if the NGO exists and is verified
            try:
                ngo = NGO.objects.get(email=email)
                if not ngo.is_verified:
                    messages.error(request, "Your NGO account is pending verification by admin. Please wait for approval.")
                    return redirect('login_ngo')
                
                # Check if the user account is active
                if not ngo.user.is_active:
                    messages.error(request, "Your account has not been activated yet. Please wait for admin verification.")
                    return redirect('login_ngo')
                
            except NGO.DoesNotExist:
                messages.error(request, "NGO profile not found. Please contact the administrator.")
                return redirect('login_ngo')
            
            # If we reach here, the NGO is verified and the password is correct
            # Authenticate and login the user
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                request.session['user_id'] = signup_ngo.id
                request.session['user_name'] = signup_ngo.ngo_name
                request.session['is_ngo'] = True
                messages.success(request, "Login successful!")
                return redirect('ngo_profile_self')
            else:
                messages.error(request, "Authentication failed. Please wait for admin verification.")
        
        except SignupNGO.DoesNotExist:
            messages.error(request, "NGO with this email does not exist!")

    return render(request, "main/login_ngo.html")

def signup_ngo(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Extract data from form
                ngo_name = request.POST.get('ngo_name', '').strip()
                registration_number = request.POST.get('registration_number', '').strip()
                category = request.POST.get('category', '').strip().lower()
                email = request.POST.get('email', '').strip()
                password = request.POST.get('password', '').strip()
                confirm_password = request.POST.get('confirm_password', '').strip()
                contact_number = request.POST.get('contact_number', '').strip()
                address = request.POST.get('address', '').strip()
                mission = request.POST.get('mission', '').strip()
                bank_name = request.POST.get('bank_name', '').strip()
                account_number = request.POST.get('account_number', '').strip()
                ifsc_code = request.POST.get('ifsc_code', '').strip()
                ngo_profile_image = request.FILES.get('ngo_profile_image')
                ngo_certificate = request.FILES.get('ngo_certificate')

                # Check if NGO is pre-registered
                try:
                    pre_registered = PreRegisteredNGO.objects.get(registration_number=registration_number)
                    
                    # Validate NGO name matches exactly
                    if pre_registered.ngo_name.lower() != ngo_name.lower():
                        messages.error(request, "NGO name does not match the pre-registered details.")
                        return redirect('signup_ngo')
                    
                    # Validate category matches exactly
                    if pre_registered.category != category:
                        messages.error(request, "Category does not match the pre-registered details.")
                        return redirect('signup_ngo')
                        
                except PreRegisteredNGO.DoesNotExist:
                    messages.error(request, "Your NGO is not in the pre-registered list. Please contact the administrator.")
                    return redirect('signup_ngo')

                # Validate password match
                if password != confirm_password:
                    messages.error(request, "Passwords do not match.")
                    return redirect('signup_ngo')

                # Check if email is already registered
                if User.objects.filter(email=email).exists() or SignupNGO.objects.filter(email=email).exists():
                    messages.error(request, "Email already registered.")
                    return redirect('signup_ngo')

                # Create user account (but don't activate it yet)
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    is_active=False  # User account starts as inactive
                )

                # Create SignupNGO instance
                signup_instance = SignupNGO.objects.create(
                    ngo_name=ngo_name,
                    registration_number=registration_number,
                    category=category,
                    email=email,
                    password=make_password(password),
                    contact_number=contact_number,
                    address=address,
                    mission=mission,
                    bank_name=bank_name,
                    account_number=account_number,
                    ifsc_code=ifsc_code,
                    ngo_profile_image=ngo_profile_image,
                    ngo_certificate=ngo_certificate
                )

                # Create NGO profile with is_verified set to False
                NGO.objects.create(
                    user=user,
                    signup_ngo=signup_instance,
                    name=ngo_name,
                    email=email,
                    services=category,
                    contact_number=contact_number or None,
                    address=address or None,
                    mission=mission or None,
                    bank_name=bank_name or None,
                    account_number=account_number or None,
                    ifsc_code=ifsc_code or None,
                    ngo_profile_image=ngo_profile_image,
                    is_verified=False  # Set to False by default
                )

                messages.success(request, "NGO registration submitted successfully. Please wait for admin verification before logging in.")
                return redirect('login_ngo')

        except Exception as e:
            messages.error(request, f"Registration failed. Error: {str(e)}")
            return redirect('signup_ngo')

    return render(request, 'main/signup_ngo.html')



#********NGO LOGIN AND SIGNUP END END***********

#********NGO PART***********

@login_required
def ngo_profile(request, ngo_id=None):
    # If ngo_id is provided, get that NGO's profile
    if ngo_id:
        try:
            ngo = NGO.objects.get(id=ngo_id)
            # If viewing someone else's profile, check if it exists
            if ngo.email != request.user.email:
                # Only allow viewing, not editing
                return render(request, 'main/ngo_profile.html', {'ngo': ngo, 'view_only': True})
        except NGO.DoesNotExist:
            messages.error(request, "NGO profile not found.")
            return redirect('ngo_discovery')
    else:
        # Get the logged-in user's NGO profile
        try:
            ngo = NGO.objects.get(email=request.user.email)
        except NGO.DoesNotExist:
            messages.error(request, "NGO profile not found. Please contact the administrator.")
            return redirect('home')

    if request.method == 'POST':
        # Only allow editing if viewing own profile
        if ngo.email != request.user.email:
            messages.error(request, "You can only edit your own profile.")
            return redirect('ngo_profile', ngo_id=ngo.id)

        existing_ngo = NGO.objects.filter(email=request.POST.get('email')).first()
        
        if existing_ngo and existing_ngo != ngo:
            messages.error(request, "Another NGO with this email already exists.")
            return redirect('ngo_profile', ngo_id=ngo.id)

        # Update the fields from the form data
        ngo.name = request.POST.get('ngo_name')
        ngo.mission = request.POST.get('mission')
        ngo.contact_number = request.POST.get('contact_number')
        ngo.email = request.POST.get('email')

        # Handle optional website and social media URLs
        ngo.website = request.POST.get('website') if request.POST.get('website') else None
        ngo.facebook = request.POST.get('facebook') if request.POST.get('facebook') else None
        ngo.instagram = request.POST.get('instagram') if request.POST.get('instagram') else None
        ngo.other_social = request.POST.get('other_social') if request.POST.get('other_social') else None

        ngo.address = request.POST.get('address')
        ngo.bank_name = request.POST.get('bank_name')
        ngo.account_number = request.POST.get('account_number')
        ngo.ifsc_code = request.POST.get('ifsc_code')

        # Don't update services - NGO services are fixed after registration
        # ngo.services = request.POST.getlist('services')

        # Handle document upload
        if 'documents' in request.FILES:
            ngo.registration_certificate = request.FILES['documents']

        ngo.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('ngo_profile', ngo_id=ngo.id)

    return render(request, 'main/ngo_profile.html', {'ngo': ngo, 'view_only': False})

@login_required
def ngo_profile_self(request):
    """View for accessing logged-in NGO's own profile without needing to specify the ID"""
    try:
        ngo = NGO.objects.get(email=request.user.email)
        return redirect('ngo_profile', ngo_id=ngo.id)
    except NGO.DoesNotExist:
        messages.error(request, "NGO profile not found. Please contact the administrator.")
        return redirect('home')

#********NGO PART END END***********

def home(request):
    return render(request, 'main/home.html')

def ngo_discovery(request):
    # Get the selected categories from the query parameters
    selected_categories = request.GET.get('categories', '').split(',')
    
    # If categories are selected, filter NGOs by those categories
    if selected_categories and selected_categories != ['']:  # Check for an empty string in the list
        ngos = NGO.objects.filter(services__in=selected_categories, is_verified=True)
    else:
        ngos = NGO.objects.filter(is_verified=True)  # Display only verified NGOs
    
    return render(request, 'main/ngo_discovery.html', {'ngos': ngos})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Donation

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum  # Import Sum for aggregation
from .models import Donation


@login_required
def donation_tracking(request):
    # Get user's donations
    donations = Donation.objects.filter(user=request.user).order_by('-donated_at')
    
    # Calculate summary statistics
    total_donation = donations.aggregate(total=Sum('amount'))['total'] or 0
    unique_ngos = donations.values('ngo').distinct().count()
    unique_categories = donations.values('ngo__services').distinct().count()
    
    # Get user's volunteer applications using email
    pending_applications = Volunteer.objects.filter(
        contact=request.user.email,  # Use email to track applications
        status='pending'
    ).select_related('ngo').order_by('-created_at')
    
    # Get approved applications
    approved_applications = Volunteer.objects.filter(
        contact=request.user.email,  # Use email to track applications
        status='approved'
    ).select_related('ngo').order_by('-created_at')
    
    # Get rejected applications
    rejected_applications = Volunteer.objects.filter(
        contact=request.user.email,  # Use email to track applications
        status='rejected'
    ).select_related('ngo').order_by('-created_at')

    context = {
        'donations': donations,
        'total_donation': total_donation,
        'unique_ngos': unique_ngos,
        'unique_categories': unique_categories,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'main/donation_tracking.html', context)




def about(request):
    return render(request, 'main/about.html')

def ngo_base(request):
    return render(request, 'main/ngo_base.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Compose email
        email_subject = f'Contact Form: {subject}'
        email_message = f'''
        New contact form submission:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        '''
        
        try:
            # Send email
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,  # From email
                ['samarthan1313@gmail.com'],  # To email
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, "Failed to send message. Please try again later.")
            
        return redirect('contact')
        
    return render(request, 'main/contact.html')



@login_required
def ngo_donations(request):
    try:
        ngo = NGO.objects.get(email=request.user.email)
    except ObjectDoesNotExist:
        messages.error(request, "NGO profile not found. Please contact the administrator.")
        return redirect('home')
    
    donations = Donation.objects.filter(ngo=ngo).order_by('-donated_at')
    expenses = Expense.objects.filter(ngo=ngo).order_by('-transaction_date')  # Corrected field name
    
    total_donations = donations.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_donations - total_expenses
    
    context = {
        'ngo': ngo,
        'total_donations': total_donations,
        'total_expenses': total_expenses,
        'balance': balance,
        'donations': donations,
        'expenses': expenses,
    }
    
    return render(request, 'main/ngo_donations.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Expense, NGO
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from .models import NGO, Expense

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def add_expense(request):
    if request.method == 'POST':
        try:
            ngo = NGO.objects.get(email=request.user.email)
        except ObjectDoesNotExist:
            messages.error(request, "NGO profile not found. Please contact the administrator.")
            return redirect('home')

        amount = request.POST.get('amount')
        transaction_date = request.POST.get('transaction_date')
        description = request.POST.get('description')
        bill_photo = request.FILES.get('bill_photo')

        # Validate fields
        if not all([amount, transaction_date, description]):
            messages.error(request, "All fields are required.")
            return redirect('ngo_donations')

        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, "Amount must be a positive number.")
                return redirect('ngo_donations')
        except ValueError:
            messages.error(request, "Invalid amount entered.")
            return redirect('ngo_donations')

        try:
            # Save expense
            expense = Expense(
                ngo=ngo,
                amount=amount,
                transaction_date=transaction_date,
                description=description,
                bill_photo=bill_photo
            )
            expense.save()
            messages.success(request, "Expense added successfully!")
            return redirect('ngo_donations')
        except Exception as e:
            logger.error(f"Error saving expense: {e}")
            messages.error(request, "An error occurred while adding the expense.")
            return redirect('ngo_donations')

    messages.error(request, "Invalid request method.")
    return redirect('ngo_donations')


def ngo_about(request):
    return render(request, 'main/ngo_about.html')

def ngo_contact(request):
    try:
        ngo = NGO.objects.get(email=request.user.email)
    except ObjectDoesNotExist:
        messages.error(request, "NGO profile not found. Please contact the administrator.")
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Send email to NGO
        try:
            send_mail(
                f'Contact Form: {subject}',
                f'From: {name} ({email})\n\nMessage:\n{message}',
                settings.DEFAULT_FROM_EMAIL,
                [ngo.email],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('ngo_contact')
        except Exception as e:
            messages.error(request, 'Failed to send message. Please try again later.')
    
    return render(request, 'main/ngo_contact.html', {'ngo': ngo})


def logout_user(request):
    # Clear NGO-specific session data if it exists
    if 'is_ngo' in request.session:
        del request.session['is_ngo']
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'user_name' in request.session:
        del request.session['user_name']
    
    # Logout the user
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect('home')

def generate_receipt(donation):
    """Generate a receipt number for a donation if it doesn't have one"""
    if not donation.receipt_number:
        donation.generate_receipt_number()
        donation.save()
    return donation.receipt_number

def handle_donation_success(request, donation):
    """Handle successful donation and generate receipt"""
    receipt_number = generate_receipt(donation)
    # Additional success handling logic here
    return receipt_number

def get_receipt(request, receipt_number):
    """API endpoint to get receipt details"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    donation = get_object_or_404(Donation, receipt_number=receipt_number)
    
    # Ensure user can only access their own receipts
    if donation.user != request.user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    receipt_data = {
        'receipt_number': donation.receipt_number,
        'donated_at': donation.donated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'ngo_name': donation.ngo.name,
        'amount': str(donation.amount),
        'donor_name': f"{donation.user.first_name} {donation.user.last_name}",
        'generated_at': donation.receipt_generated_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return JsonResponse(receipt_data)

@login_required
def volunteer_registration(request):
    # Get only verified NGOs
    registered_ngos = NGO.objects.filter(is_verified=True).order_by('name')
    
    context = {
        'ngos': registered_ngos,
    }
    return render(request, 'main/volunteer_registration.html', context)

@login_required
def register_volunteer(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            contact = request.user.email  # Use user's email as contact
            address = request.POST.get('address')
            days = request.POST.getlist('days[]')
            time_slot = request.POST.get('timeSlot')
            ngo_id = request.POST.get('selected_ngo')

            # Validate data
            if not all([name, address, days, time_slot, ngo_id]):
                messages.error(request, 'Please fill all required fields.')
                return redirect('volunteer_registration')

            # Get NGO instance
            ngo = NGO.objects.get(id=ngo_id)

            # Create new volunteer with pending status
            volunteer = Volunteer.objects.create(
                name=name,
                contact=contact,  # Store user's email
                address=address,
                preferred_days=days,
                preferred_time=time_slot,
                ngo=ngo,
                status='pending'  # Set initial status as pending
            )

            messages.success(request, 'Your volunteer application has been submitted and is pending approval.')
            return redirect('donation_tracking')

        except NGO.DoesNotExist:
            messages.error(request, 'Selected NGO does not exist.')
            return redirect('volunteer_registration')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('volunteer_registration')

    return redirect('volunteer_registration')

@login_required
def ngo_volunteer(request):
    if not request.session.get('is_ngo'):
        messages.error(request, "Access denied. NGO login required.")
        return redirect('login_ngo')
    
    # Get the NGO associated with the logged-in user
    try:
        ngo = NGO.objects.get(email=request.user.email)
    except NGO.DoesNotExist:
        messages.error(request, "NGO profile not found. Please contact the administrator.")
        return redirect('home')
    
    # Get pending and active volunteers
    pending_volunteers = Volunteer.objects.filter(ngo=ngo, status='pending')
    active_volunteers = Volunteer.objects.filter(ngo=ngo, status='approved')
    
    context = {
        'pending_volunteers': pending_volunteers,
        'active_volunteers': active_volunteers,
    }
    
    return render(request, 'main/ngo_volunteer.html', context)

@login_required
def update_volunteer_status(request, volunteer_id):
    if not request.session.get('is_ngo'):
        messages.error(request, "Access denied. NGO login required.")
        return redirect('login_ngo')
    
    volunteer = get_object_or_404(Volunteer, id=volunteer_id)
    try:
        ngo = NGO.objects.get(email=request.user.email)
    except NGO.DoesNotExist:
        messages.error(request, "NGO profile not found. Please contact the administrator.")
        return redirect('home')
    
    # Verify that the volunteer belongs to this NGO
    if volunteer.ngo != ngo:
        messages.error(request, "Access denied. This volunteer does not belong to your NGO.")
        return redirect('ngo_volunteer')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['approved', 'rejected']:
            volunteer.status = new_status
            volunteer.save()
            
            # Send email notification to volunteer
            try:
                if new_status == 'approved':
                    subject = 'Volunteer Application Approved'
                    message = f'Dear {volunteer.name},\n\nYour volunteer application for {ngo.name} has been approved. We look forward to working with you!\n\nBest regards,\n{ngo.name} Team'
                else:
                    subject = 'Volunteer Application Status Update'
                    message = f'Dear {volunteer.name},\n\nYour volunteer application for {ngo.name} has been reviewed. We regret to inform you that we cannot accept your application at this time.\n\nBest regards,\n{ngo.name} Team'
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [volunteer.contact],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {str(e)}")
            
            if new_status == 'approved':
                messages.success(request, f"Volunteer {volunteer.name} has been approved.")
            else:
                messages.success(request, f"Volunteer {volunteer.name} has been removed.")
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('ngo_volunteer')

def ngo_details(request, ngo_id):
    try:
        ngo = NGO.objects.get(id=ngo_id)
        return render(request, 'main/ngo_details.html', {'ngo': ngo})
    except NGO.DoesNotExist:
        messages.error(request, "NGO not found.")
        return redirect('ngo_discovery')

def terms(request):
    return render(request, 'main/terms.html')

def privacy(request):
    return render(request, 'main/privacy.html')

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_user_info(request):
    # Get all users who signed up as regular users (not NGOs)
    users = User.objects.filter(
        is_staff=False,
        email__in=SignupUser.objects.values_list('email', flat=True)
    )
    
    # Calculate total users
    total_users = users.count()
    
    # Calculate active users (logged in within last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_users = users.filter(last_login__gte=thirty_days_ago).count()
    
    # Calculate total donations from regular users
    total_donations = Donation.objects.filter(user__in=users).aggregate(total=Sum('amount'))['total'] or 0
    
    # Annotate users with their total donations
    users = users.annotate(
        total_donations=Sum('donation__amount')
    ).order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'total_donations': total_donations,
    }
    
    return render(request, 'main/admin_user_info.html', context)

@user_passes_test(is_admin)
def admin_remove_user(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, is_staff=False)
            user.delete()
            messages.success(request, f'User {user.get_full_name()} has been removed successfully.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    
    return redirect('admin_user_info')

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check for hardcoded admin credentials
        if username == 'Samarthan13' and password == 'Samarthan13@':
            # Get or create admin user
            try:
                admin_user = User.objects.get(username=username)
            except User.DoesNotExist:
                admin_user = User.objects.create_superuser(
                    username=username,
                    password=password,
                    email='samarthan1313@gmail.com'
                )
                admin_user.is_staff = True
                admin_user.save()
            
            # Authenticate and login
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Admin login successful!")
                return redirect('admin_user_info')  # Redirect to admin dashboard
        
        messages.error(request, "Invalid credentials!")
        return redirect('admin_login')
    
    # If user is already logged in as admin, redirect to dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_user_info')
    
    return render(request, 'main/admin_login.html')

@user_passes_test(is_admin)
def admin_logout(request):
    logout(request)
    messages.success(request, "Admin logged out successfully!")
    return redirect('admin_login')

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get statistics for the dashboard
    total_users = User.objects.filter(is_staff=False).count()
    total_ngos = NGO.objects.count()
    total_donations = Donation.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_volunteers = Volunteer.objects.filter(status='approved').count()
    
    # Get recent activities
    recent_donations = Donation.objects.select_related('user', 'ngo').order_by('-donated_at')[:5]
    recent_ngos = NGO.objects.order_by('-id')[:5]  # Order by most recently added
    
    context = {
        'total_users': total_users,
        'total_ngos': total_ngos,
        'total_donations': total_donations,
        'total_volunteers': total_volunteers,
        'recent_donations': recent_donations,
        'recent_ngos': recent_ngos,
    }
    
    return render(request, 'main/admin_dashboard.html', context)

@user_passes_test(is_admin)
def admin_ngo_info(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')

    # Get all NGOs with their signup information
    ngos = NGO.objects.select_related('signup_ngo', 'user').all()
    
    # Fix missing registration numbers
    for ngo in ngos:
        if ngo.registration_number is None and ngo.signup_ngo:
            ngo.registration_number = ngo.signup_ngo.registration_number
            ngo.save()
            
    total_ngos = ngos.count()
    verified_ngos = ngos.filter(is_verified=True).count()
    pending_ngos = total_ngos - verified_ngos
    total_ngo_donations = Donation.objects.filter(ngo__in=ngos).aggregate(Sum('amount'))['amount__sum'] or 0

    # Get total volunteers for each NGO
    for ngo in ngos:
        ngo.total_volunteers = Volunteer.objects.filter(ngo=ngo).count()
        ngo.total_received_donations = Donation.objects.filter(ngo=ngo).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'ngos': ngos,
        'total_ngos': total_ngos,
        'verified_ngos': verified_ngos,
        'pending_ngos': pending_ngos,
        'total_ngo_donations': total_ngo_donations
    }
    return render(request, 'main/admin_ngo_info.html', context)

@user_passes_test(is_admin)
def admin_verify_ngo(request, ngo_id):
    try:
        with transaction.atomic():
            ngo = get_object_or_404(NGO, id=ngo_id)
            
            # Activate the user account
            user = ngo.user
            user.is_active = True
            user.save()
            
            # Verify the NGO
            ngo.is_verified = True
            ngo.save()
            
            # Update the Django user's password if it doesn't match the SignupNGO password
            # This ensures the user can login with their original password
            if ngo.signup_ngo:
                try:
                    # Get the raw password from the SignupNGO model
                    signup_ngo = ngo.signup_ngo
                    
                    # Set the username to match the email for consistency
                    user.username = ngo.email
                    user.email = ngo.email
                    user.save()
                    
                except Exception as e:
                    logger.error(f"Error updating user credentials: {str(e)}")
            
            # Send verification email
            try:
                send_mail(
                    'NGO Account Verified - SAMARTHAN',
                    f'''Dear {ngo.name},

Your NGO account has been verified by our admin team. You can now log in to your account using your registered email and password.

Best regards,
SAMARTHAN Team''',
                    settings.DEFAULT_FROM_EMAIL,
                    [ngo.email],
                    fail_silently=True,
                )
            except Exception as e:
                # Log the error but don't stop the verification process
                logger.error(f"Failed to send verification email to {ngo.email}: {str(e)}")
            
            messages.success(request, f'NGO "{ngo.name}" has been verified successfully.')
    except Exception as e:
        messages.error(request, f'Error verifying NGO: {str(e)}')
    return redirect('admin_ngo_info')

@user_passes_test(is_admin)
def admin_remove_ngo(request, ngo_id):
    ngo = get_object_or_404(NGO, id=ngo_id)
    ngo_name = ngo.name
    ngo.delete()
    messages.success(request, f'NGO "{ngo_name}" has been removed successfully.')
    return redirect('admin_ngo_info')


@user_passes_test(is_admin)
def admin_ngo_details(request, ngo_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')

    try:
        ngo = NGO.objects.select_related('signup_ngo').get(id=ngo_id)
        # Use the registration number from signup_ngo if the NGO's registration_number is None
        if ngo.registration_number is None and ngo.signup_ngo:
            ngo.registration_number = ngo.signup_ngo.registration_number
            ngo.save()
            
        return render(request, 'main/admin_ngo_details.html', {
            'ngo': ngo,
            'registration_certificate_url': ngo.signup_ngo.ngo_certificate.url if ngo.signup_ngo and ngo.signup_ngo.ngo_certificate else None,
        })
    except NGO.DoesNotExist:
        messages.error(request, 'NGO not found.')
        return redirect('admin_ngo_info')

@user_passes_test(is_admin)
def admin_donations(request):
    donations = Donation.objects.select_related('user', 'ngo').order_by('-donated_at')
    context = {
        'donations': donations,
    }
    return render(request, 'main/admin_donations.html', context)