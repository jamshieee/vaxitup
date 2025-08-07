from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth import logout
from django.utils import timezone
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import *
from django.db.models import Count, Min, OuterRef, Subquery, F
from .forms import *
from django.contrib import messages
from .forms import CenterRegistrationForm
from functools import wraps
from datetime import datetime, date, timedelta
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.conf import settings
import json, random




# Create your views here.
def index(request):
    return render(request,'user/page1.html')

def register(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        errors = {}

        # Validate name
        if not name:
            errors["name_error"] = "Name is required."

        # Validate email
        if not email:
            errors["email_error"] = "Email is required."
        else:
            try:
                EmailValidator()(email)
            except ValidationError:
                errors["email_error"] = "Invalid email format."

        # Validate phone number (must be 10 digits)
        if not phone:
            errors["phone_error"] = "Phone number is required."
        elif not phone.isdigit() or len(phone) != 10:
            errors["phone_error"] = "Phone number must be exactly 10 digits."

        # Validate password
        if not password:
            errors["password_error"] = "Password is required."
        elif password != confirm_password:
            errors["password_error"] = "Passwords do not match."
        else:
            try:
                validate_password(password)
            except ValidationError as e:
                errors["password_error"] = " ".join(e.messages)

        # Check if email, phone, or name are already taken
        if Userreg.objects.filter(email=email).exists():
            errors["email_error"] = "Email already registered."

        if Userreg.objects.filter(phone=phone).exists():
            errors["phone_error"] = "Phone number already registered."

        if Userreg.objects.filter(Name=name).exists():
            errors["name_error"] = "Name already taken. Try another one."

        # If validation errors exist, return them
        if errors:
            return render(request, "user/register.html", {
                "errors": errors,
                "name": name,
                "email": email,
                "phone": phone
            })

        # Hash password securely
        hashed_password = make_password(password)

        # Generate OTP and set expiry time (5 minutes)
        otp_code = str(random.randint(100000, 999999))
        otp_expiry_time = now() + timedelta(minutes=5)

        # Store temporary user data in session
        request.session["temp_user"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "otp": otp_code,
            "otp_expiry": otp_expiry_time.isoformat(),
        }

        # Send OTP via email
        send_mail(
            "Your OTP Code",
            f"Your OTP is: {otp_code}. It expires in 5 minutes.",
            "your-email@example.com",
            [email],
            fail_silently=False,
        )

        return redirect("verify_otp")

    return render(request, "user/register.html", {"errors": {}})

def verify_otp(request):
    temp_user = request.session.get("temp_user")
    
    if not temp_user:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = temp_user.get("otp")
        otp_expiry = temp_user.get("otp_expiry")

        if now() > datetime.fromisoformat(otp_expiry):
            messages.error(request, "OTP expired. Click 'Resend OTP' to get a new one.")
            return redirect("verify_otp")

        if entered_otp == stored_otp:
            # Save user to database
            user = Userreg.objects.create(
                Name=temp_user["name"],
                email=temp_user["email"],
                phone=temp_user["phone"],
                password=temp_user["password"],
            )

            # Clear session data
            del request.session["temp_user"]

            messages.success(request, "Registration successful! You can now log in.")
            return redirect("DBLogin")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "user/verify_otp.html", {"email": temp_user["email"]})

def resend_otp(request):
    temp_user = request.session.get("temp_user")
    
    if not temp_user:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    new_otp = str(random.randint(100000, 999999))
    temp_user["otp"] = new_otp
    temp_user["otp_expiry"] = (now() + timedelta(minutes=5)).isoformat()

    request.session["temp_user"] = temp_user

    send_mail(
        "Your New OTP Code",
        f"Your new OTP is: {new_otp}. It expires in 5 minutes.",
        "your-email@example.com",
        [temp_user["email"]],
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify_otp")

def DBLogin(request): 
    template = "user/login.html"

    if request.method == "POST": 
        email = request.POST.get("txtEmail", "").strip()  # Strip spaces
        password = request.POST.get("txtPassword", "").strip()

        try: 
            # 🔹 Check if user exists
            user_obj = Userreg.objects.filter(email=email).first()

            if user_obj:
                
                
                if check_password(password, user_obj.password):  # Verify hashed password
                    request.session["user_id"] = user_obj.id  
                    request.session["USERNAME"] = user_obj.Name  
                    return redirect("homeuser")  
                else:
                    return render(request, template, {"error": "Invalid password"})
            else:
                
                return render(request, template, {"error": "User not found"})
                
        except Exception as e: 
            
            return render(request, template, {"error": f"An error occurred: {str(e)}"})

    return render(request, template)

# Store OTPs temporarily
otp_storage = {}

def forgot_password(request):
    return render(request, "user/forgot_password.html")

def send_reset_otp(request):
    if request.method == "POST":
        email = request.POST["email"]
        user = Userreg.objects.filter(email=email).first()

        if user:
            otp = random.randint(100000, 999999)
            cache.set(f"otp_{email}", {"otp": otp, "time": timezone.now()}, timeout=300)  # ✅ Fixed cache usage
            
            send_mail(
                "Password Reset OTP",
                f"Your OTP is {otp}. It expires in 5 minutes.",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "OTP sent to your email.")
            return render(request, "user/change_password.html", {"email": email})
        else:
            messages.error(request, "No account found with this email.")
            return redirect("forgot_password")

def verify_reset_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        entered_otp = request.POST.get("otp")
        new_password = request.POST.get("password")

        otp_data = cache.get(f"otp_{email}")  # Retrieve OTP data from cache

        if otp_data:
            stored_otp = otp_data["otp"]
            otp_time = otp_data["time"]

            if stored_otp == int(entered_otp) and timezone.now() - otp_time <= timedelta(minutes=5):
                user = Userreg.objects.get(email=email)
                user.password = make_password(new_password)  # Hash password before saving
                user.save()

                cache.delete(f"otp_{email}")  # ✅ Remove OTP after successful reset
                messages.success(request, "Password reset successful. Please log in.")
                return redirect("DBLogin")
            else:
                messages.error(request, "Invalid OTP or OTP expired.")
        else:
            messages.error(request, "OTP expired or not found.")

        return render(request, "user/change_password.html", {"email": email})

    return redirect("forgot_password")  # Handle GET requests properly
    

def user_logout(request):
    logout(request)  
    request.session.flush()  # Clears session
    return redirect("DBLogin")  # Redirect to user login page

def userlog(request):
    return render(request,'user/login.html')

def userreg(request):
    return render(request,'user/register.html')

def homeuser(request):
    username = request.session.get('USERNAME')
    if not username:
        return redirect('DBLogin')
    
    return render(request, 'user/home.html')

def search_vaccines(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    # Filter vaccines by availability
    unique_vaccines = Vaccines.objects.filter(availability=True)

    # Apply category filter if selected
    if category:
        unique_vaccines = unique_vaccines.filter(vaccine_category=category)

    # Apply search filter if query is provided
    if query:
        unique_vaccines = unique_vaccines.filter(vaccine_name__icontains=query)

    # Group by vaccine name and get minimum ID record
    unique_vaccines = (
        unique_vaccines.values("vaccine_name")
        .annotate(
            min_id=Min("id"),
            vaccine_category=Min("vaccine_category"),
            vaccine_details=Min("vaccine_details"),
            doses=Min("doses"),
        )
    )

    return render(request, "user/search_vaccines.html", {"vaccines": unique_vaccines, "query": query})

def select_center(request):
    query = request.GET.get("q", "").strip()
    vaccine_name = request.GET.get("vaccine", "").strip()

    if not vaccine_name:
        return render(request, "user/search_center.html", {"centers": [], "query": query, "selected_vaccine": None})

    # Get centers that provide the selected vaccine
    centers = Healthcenters.objects.filter(
        is_verified=True, 
        is_approved=True, 
        id__in=Vaccines.objects.filter(vaccine_name=vaccine_name).values("center_id")
    )

    # Apply search filter before rendering
    if query:
        centers = centers.filter(center_name__icontains=query)

    return render(request, "user/search_center.html", {"centers": centers, "query": query, "selected_vaccine": vaccine_name})


def check_vaccine_availability(request):
    center_id = request.GET.get("center_id")
    vaccine_id = request.GET.get("vaccine_id")

    # Check if the center exists
    try:
        center = Healthcenters.objects.get(center_id=center_id)
    except Healthcenters.DoesNotExist:
        return JsonResponse({"available": False, "message": "Invalid center"})

    # Check if the vaccine is available at the selected center
    is_available = Vaccines.objects.filter(id=vaccine_id, center=center).exists()

    return JsonResponse({"available": is_available})

def USERProfile(request):
    username = request.session.get('USERNAME')
    if not username:
        return redirect('DBLogin')

    try:
        profile = Userreg.objects.get(Name=username)
    except Userreg.DoesNotExist:
        return redirect('DBLogin')

    # Fetch user's booking history and prioritize pending bookings
    bookings = BookingDetails.objects.filter(user=profile).order_by(
        models.Case(
            models.When(status="pending", then=0),
            default=1,
            output_field=models.IntegerField(),
        ),
        "date",
    )

    return render(request, "user/profile.html", {"profile": profile, "bookings": bookings})

def update_profile(request):
    if request.method == "POST":
        username = request.session.get("USERNAME")

        # Debug: Check if username is fetched from session
        if not username:
            return JsonResponse({"success": False, "message": "Session expired. Please log in again."})

        try:
            profile = Userreg.objects.get(Name__iexact=username)  # Case-insensitive lookup
        except Userreg.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})

        new_name = request.POST.get("name").strip()
        new_email = request.POST.get("email").strip()
        new_phone = request.POST.get("phone").strip()

        # Ensure username uniqueness
        if new_name != profile.Name and Userreg.objects.filter(Name__iexact=new_name).exclude(id=profile.id).exists():
            return JsonResponse({"success": False, "message": "Username already exists!"})

        # Update values
        profile.Name = new_name
        profile.email = new_email
        profile.phone = new_phone
        profile.save()  # Ensure save is called

        # Update session username
        request.session["USERNAME"] = new_name

        return JsonResponse({"success": True, "message": "Profile updated successfully", "name": new_name, "email": new_email, "phone": new_phone})

    return JsonResponse({"success": False, "message": "Invalid request"})


def cancel_booking(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(BookingDetails, id=booking_id)

        if booking.status == "pending":  # Allow rejection only if status is pending
            booking.status = "cancelled"
            booking.save()
            messages.success(request, "Booking cancelled successfully.")
        else:
            messages.error(request, "Only pending bookings can be cancelled.")

    return redirect("USERProfile")  # Redirect back to the profile page

def feedback_view(request):
    return render(request, "user/feedback.html")

def submit_feedback(request):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            messages.error(request, "User not logged in.")
            return redirect("feedback_view")

        user = Userreg.objects.get(id=user_id)
        feedback_text = request.POST.get("feedback")
        rating = request.POST.get("rating")

        if not feedback_text or not rating:
            messages.error(request, "All fields are required.")
            return redirect("feedback_view")

        # Save feedback
        Feedback.objects.create(user=user, feedback=feedback_text, rating=int(rating))

        messages.success(request, "Thank you for your feedback! 😊")
        return redirect("feedback_view")  # Ensure this URL name exists

    return redirect("feedback_view")

def confirm_booking(request):
    username = request.session.get("USERNAME")
    if not username:
        messages.error(request, "Please log in to book a vaccine.")
        return redirect("DBLogin")

    try:
        user = Userreg.objects.get(Name=username)
    except Userreg.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("DBLogin")

    center_name = request.GET.get("center_name", "").strip()
    selected_vaccine_name = request.GET.get("vaccine", "").strip()

    if not center_name or not selected_vaccine_name:
        messages.error(request, "Invalid request! Center or vaccine is missing.")
        return redirect("homeuser")

    center = Healthcenters.objects.filter(center_name=center_name).first()
    if not center:
        messages.error(request, "Selected center is not available.")
        return redirect("homeuser")

    vaccine = Vaccines.objects.filter(center=center, vaccine_name=selected_vaccine_name).first()
    if not vaccine:
        messages.error(request, "The selected vaccine is not available at this center.")
        return redirect("homeuser")

    form_data = {}
    errors = {}

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        age = request.POST.get("age", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        aadhaar = request.POST.get("aadhaar", "").strip()
        dose = request.POST.get("doses", "").strip()
        selected_date = request.POST.get("date", "").strip()
        selected_time = request.POST.get("time", "").strip()

        form_data = {
            "name": name, "age": age, "email": email, "phone": phone,
            "aadhaar": aadhaar, "dose": dose, "date": selected_date, "time": selected_time
        }

        # ✅ Convert selected date to a date object
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            errors["date"] = "Invalid date format."

        # ✅ Ensure the user is booking at least 30 days after the last booking
        if not errors.get("date"):
            last_booking = BookingDetails.objects.filter(aadhaar=aadhaar).order_by("-date").first()

        if last_booking:
            allowed_booking_date = last_booking.date + timedelta(days=30)
            if selected_date_obj < allowed_booking_date:
                days_remaining = (allowed_booking_date - selected_date_obj).days
                errors["date"] = f"You can only book another vaccine after {allowed_booking_date.strftime('%d-%m-%Y')} ({days_remaining} days remaining), even at another center."

        # ✅ Prevent booking past dates
        if "date" not in errors and selected_date_obj < now().date():
            errors["date"] = "You cannot book for past dates."

        # ✅ Validate Aadhaar number
        if not aadhaar.isdigit() or len(aadhaar) != 12:
            errors["aadhaar"] = "Aadhaar number must be exactly 12 digits."
        elif aadhaar[0] in "01":
            errors["aadhaar"] = "Aadhaar number cannot start with 0 or 1."

        # ✅ Ensure all required fields are filled
        if not all([name, age, email, phone, aadhaar, dose, selected_date, selected_time]):
            errors["general"] = "All fields are required."

        try:
            age = int(age)
            if age > 120:
                errors["age"] = "Age must be less than 120."
        except ValueError:
            errors["age"] = "Age must be a valid number."

        if not name.replace(" ", "").isalpha():
            errors["name"] = "Name must contain only letters."

        if not phone.isdigit() or len(phone) != 10:
            errors["phone"] = "Phone number must be exactly 10 digits."

        try:
            selected_time_obj = datetime.strptime(selected_time, "%I:%M %p").time()
        except ValueError:
            errors["time"] = "Invalid time format. Please select a valid time."

        category = vaccine.vaccine_category
        if category == "Child Vaccination" and age > 12:
            errors["age"] = "This vaccine is only for children under 12."
        elif category == "Adult Vaccination" and (age < 13 or age > 59):
            errors["age"] = "This vaccine is for ages 13-59."
        elif category == "Flu Vaccination" and age < 60:
            errors["age"] = "This vaccine is for 60+ individuals."
        elif category == "Pregnant Women" and age < 18:
            errors["age"] = "This vaccine is for adult women."

                # ✅ Prevent booking the same vaccine with the same dose twice
        if BookingDetails.objects.filter(aadhaar=aadhaar, vaccine_name=selected_vaccine_name, dose=dose).exists():
            errors["dose"] = f"You have already booked Dose {dose} for this vaccine."

        # ✅ Prevent booking the same vaccine at another center
        if BookingDetails.objects.filter(aadhaar=aadhaar, vaccine_name=selected_vaccine_name).exists():
            errors["vaccine"] = "You have already booked this vaccine at another center."

        # ✅ Prevent booking a dose that does not exist for the selected vaccine
        try:
            dose = int(dose)  # Convert selected dose to integer
            vaccine_doses = int(vaccine.doses)  # Convert vaccine doses to integer (if it's stored as string)
            
            if dose > vaccine_doses:  # Ensure the user doesn't exceed the allowed doses
                errors["dose"] = f"This vaccine only has {vaccine_doses} dose(s). You cannot book Dose {dose}."
        except ValueError:
            errors["dose"] = "Invalid dose selection. Please select a valid dose."

        # ✅ Prevent booking on center holidays
        if CenterHoliday.objects.filter(center=center, date=selected_date_obj).exists():
            errors["date"] = "The selected date is a holiday for this center."

        # ✅ Prevent booking the same time slot on the same date
        if BookingDetails.objects.filter(center=center, date=selected_date_obj, time=selected_time_obj).exists():
            errors["time"] = "This time slot is already booked."


        if errors:
            return render(request, "user/confirm_booking.html", {
                "selected_center": center.center_name,
                "selected_vaccine": selected_vaccine_name,
                "form_data": form_data,
                "errors": errors,
            })

        # ✅ Generate token number
        existing_bookings = BookingDetails.objects.filter(center=center, date=selected_date_obj)
        token_number = f"D{str(existing_bookings.count() + 1).zfill(3)}"

        # ✅ Save booking
        booking = BookingDetails.objects.create(
            user=user, name=name, age=age, email=email, phone=phone, aadhaar=aadhaar,
            center=center, vaccine_name=selected_vaccine_name, dose=int(dose),
            date=selected_date_obj, time=selected_time_obj
        )

        # ✅ Send email notification
        subject = "Vaccine Booking Confirmation"
        message = (
            f"Dear {name},\n\n"
            f"Your vaccine booking has been confirmed.\n\n"
            f"Details:\n"
            f"- Center: {center.center_name}\n"
            f"- Vaccine: {selected_vaccine_name}\n"
            f"- Date: {selected_date}\n"
            f"- Time: {selected_time}\n"
            f"- Token: {token_number}\n\n"
            f"If you are unable to attend, please cancel your booking in your profile to free up the time slot for others.\n\n"
            f"Thank you,\nVaccine Booking Team"
        )

        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email], fail_silently=False)
        except Exception as e:
            print(f"Email sending failed: {e}")

        return render(request, "user/confirm_booking.html", {
            "selected_center": center.center_name,
            "selected_vaccine": selected_vaccine_name,
            "form_data": {},
            "errors": {},
            "token_number": token_number,
        })

    return render(request, "user/confirm_booking.html", {
        "selected_center": center.center_name,
        "selected_vaccine": selected_vaccine_name,
    })


def user_notifications(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("/DBLogin/")  # Redirect if not logged in

    notifications = Notification.objects.filter(user_id=user_id).order_by("-created_at")

    # ✅ Store the last time the user viewed notifications
    request.session["last_notification_check"] = now().isoformat()

    return render(request, "user/notification.html", {
        "notifications": notifications,
        "unread_count": len(notifications)  # Send unread count for badge
    })


def user_notifications_json(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    # Fetch all notifications
    notifications = Notification.objects.filter(user_id=user_id).order_by("-created_at")

    # Get the last notification check timestamp
    last_check = request.session.get("last_notification_check", "2000-01-01T00:00:00")  # Default to old date

    # Get only unread notifications
    unread_notifications = [n for n in notifications if n.created_at.isoformat() > last_check]

    notifications_data = [
        {
            "center_name": notification.health_center.center_name if notification.health_center else "Unknown",
            "message": notification.message,
            "document_url": notification.document.url if notification.document else None,
            "timestamp": notification.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for notification in unread_notifications
    ]

    return JsonResponse({
        "notifications": notifications_data,
        "unread_count": len(unread_notifications)  # Send unread count separately
    })

#admin views
def DBAdmin(request):
    template = loader.get_template("admin/admin_login.html")
    context = {}
    
    # Hardcoded admin credentials
    admin_username = "vaxitup"
    admin_password = "vaxitup@786"
    
    if request.method == "POST":
        username = request.POST.get('txtUname')
        password = request.POST.get('txtPassword')
        
        # Check hardcoded credentials
        if username == admin_username and password == admin_password:
            request.session['USERNAME'] = username  # Store session for logged-in admin
            template = loader.get_template("admin/admin_home.html")
            return HttpResponse(template.render({}, request))
        else:
            context = {"error": "Invalid username or password"}
    
    return HttpResponse(template.render(context, request))

def admin_logout(request):
    logout(request)  
    request.session.flush()  # Clears session
    return redirect("DBAdmin")

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'USERNAME' not in request.session:  # Check if admin is logged in
            return redirect('/admin-login/')  # Redirect to custom login page
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_home(request):
    return render(request, 'admin/admin_home.html')
@admin_required
def center(request):
    return render(request, 'admin/approved_centers.html')

# View to manage unapproved centers
@admin_required
def manage_centers(request):
    centers = Healthcenters.objects.filter(is_approved=False)  # Only unapproved centers
    return render(request, 'admin/manage_centers.html', {'centers': centers})

@admin_required
def admin_feedback_view(request):
    feedbacks = Feedback.objects.all().order_by("-created_at")  # Get all feedback, newest first
    return render(request, "admin/admin_feedback.html", {"feedbacks": feedbacks})

@admin_required
def approve_center(request, center_id):
    center = get_object_or_404(Healthcenters, id=center_id)

    if not center.is_approved:
        center.is_approved = True
        center.is_verified = True
        center.save()

        messages.success(request, f'Center "{center.center_name}" has been approved.')

    return redirect('manage_centers')  # Redirect back to manage centers page


@admin_required
def approved_centers(request):
    centers = Healthcenters.objects.filter(is_approved=True)
    return render(request, 'admin/approved_centers.html', {'centers': centers})
@admin_required
def unapprove_center(request, center_id):
    center = get_object_or_404(Healthcenters, center_id=center_id)

    if center.is_approved:
        center.is_approved = False
        center.is_verified = False
        center.save()

        messages.success(request, f'Center "{center.center_name}" has been unapproved.')

    return redirect('approved_centers')  # Ensure this URL exists

@admin_required
def admin_users_view(request):
    """Display all registered users in the admin panel."""
    users = Userreg.objects.all()
    return render(request, 'admin/admin_users.html', {'users': users})

@admin_required
def reject_user(request, user_id):
    """Remove a user from the database."""
    user = get_object_or_404(Userreg, id=user_id)
    user.delete()
    return redirect('admin_users_view') 

@admin_required
def vaccinated_users_view(request):
    """Display users who have completed their vaccination."""
    vaccinated_users = BookingDetails.objects.filter(status="completed")
    return render(request, 'admin/vaccinated_users.html', {'vaccinated_users': vaccinated_users})

@admin_required
def delete_center(request, center_id):
    if request.method == "POST":
        center = get_object_or_404(Healthcenters, id=center_id)
        center.delete()
        return redirect("approved_centers") 



def center_registration(request):
    if request.method == "POST":
        form = CenterRegistrationForm(request.POST)
        if form.is_valid():
            center = form.save(commit=False)  # Don't commit yet
            center.password = make_password(form.cleaned_data['password'])  # Hash password
            center.is_approved = False  # Centers need admin approval
            center.save()  # Now save to DB
            messages.success(request, "Registration successful. Wait for admin approval.")
            return redirect("pending_verification")  # Redirect to a waiting page
        else:
            messages.error(request, "Invalid details. Please check your inputs.")
    else:
        form = CenterRegistrationForm()

    return render(request, "centers/CenterRegistration.html", {"form": form})


# Pending verification page
def pending_verification(request):
    return render(request, 'centers/pending_verification.html')


def check_approval_status(request):
    if 'center_id' in request.session:
        center_id = request.session['center_id']
        center = Healthcenters.objects.get(id=center_id)
        return JsonResponse({'approved': center.is_approved})
    return JsonResponse({'approved': False})

def center_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            center = Healthcenters.objects.get(username=username)

            # Use Django's check_password() to verify the hashed password
            if not check_password(password, center.password):  
                messages.error(request, "Invalid username or password.")
                return redirect("center_login")

            if not center.is_approved:
                messages.error(request, "Your center is not approved yet. Please wait for admin approval.")
                return redirect("pending_verification")

            # Store correct center_id in session
            request.session["center_id"] = center.center_id  
            request.session["center_name"] = center.center_name  

            messages.success(request, "Login successful!")
            return redirect("center_welcome")

        except Healthcenters.DoesNotExist:
            messages.error(request, "Invalid username or password.")

    return render(request, "centers/centerlog.html")

def center_logout(request):
    logout(request)  
    request.session.flush()  # Clears session
    return redirect("center_login")

def center_welcome(request):
    center_id = request.session.get('center_id')  # Ensure session stores center_id
    if not center_id:
        return redirect('center_login')  # Redirect to login if not authenticated

    try:
        center = Healthcenters.objects.get(center_id=center_id)
    except Healthcenters.DoesNotExist:
        center = None  # Handle the case where the center is not found

    return render(request, 'centers/welcome.html', {'center': center})

def center_dashboard(request):
    center_id = request.session.get("center_id")  # Get center_id from session
    
    if not center_id:
        return redirect('login')
    
    try:
        center = Healthcenters.objects.get(id=center_id)
    except Healthcenters.DoesNotExist:
        return redirect('login')
    
    # Fetch the counts for the center
    total_bookings = BookingDetails.objects.filter(center=center).count()
    completed_bookings = BookingDetails.objects.filter(center=center, status="completed").count()
    today_bookings = BookingDetails.objects.filter(center=center, date=now().date()).count()
    vaccine_count = Vaccines.objects.filter(center=center).count()
    
    return render(request, "centers/welcome.html", {
        "center_name": center.center_name,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "today_bookings": today_bookings,
        "vaccine_count": vaccine_count,
    })

    
def center_profile(request):
    center_id = request.session.get("center_id")
    if not center_id:
        messages.error(request, "You must be logged in to view the profile.")
        return redirect("center_login")

    try:
        center = Healthcenters.objects.get(center_id=center_id)
    except Healthcenters.DoesNotExist:
        messages.error(request, "Center not found.")
        return redirect("center_home")

    return render(request, "centers/center_profile.html", {"center": center})


def edit_center_profile(request, center_id):
    center = get_object_or_404(Healthcenters, center_id=center_id)

    if request.method == "POST":
        center.center_name = request.POST.get("center_name", center.center_name)
        center.phone = request.POST.get("phone", center.phone)
        center.email = request.POST.get("email", center.email)

        # Handle profile image upload
        if "profile_image" in request.FILES:
            center.profile_image = request.FILES["profile_image"]

        center.save()
        messages.success(request, "Profile updated successfully.")

        # Redirect to profile page (without center_id)
        return redirect("center_profile")

    return render(request, "centers/edit_profile.html", {"center": center})

def center_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'center_id' not in request.session:  # Check if center is logged in
            return redirect('center_login')  # Redirect to login page
        return view_func(request, *args, **kwargs)
    return wrapper

@center_required
def center_home(request):
    center_name = request.session.get('center_name', 'Unknown Center')  # Retrieve from session
    return render(request, "centers/centerhome.html", {"center_name": center_name})

@center_required
def add_vaccines(request):
    center_id = request.session.get("center_id")

    if not center_id:
        messages.error(request, "You must be logged in as a center to access this page.")
        return redirect("center_login")

    center = get_object_or_404(Healthcenters, center_id=center_id)

    # Retrieve vaccines linked to the center
    vaccines = Vaccines.objects.filter(center=center)

    if request.method == "POST":
        vaccine_category = request.POST.get("vaccine_category")
        vaccine_name = request.POST.get("vaccine_name")
        vaccine_details = request.POST.get("vaccine_details")
        doses = request.POST.get("doses")
        availability = request.POST.get("availability")  # "Yes" or "No"

        # Ensure doses is an integer
        try:
            doses = int(doses)
        except ValueError:
            messages.error(request, "Invalid input for doses. Please enter a number.")
            return redirect("add_vaccines")

        # Convert availability to boolean
        availability = True if availability == "Yes" else False

        # Check if the exact vaccine name and category exist for this center
        if Vaccines.objects.filter(center=center, vaccine_name=vaccine_name, vaccine_category=vaccine_category).exists():
            messages.error(request, f"The vaccine '{vaccine_name}' in category '{vaccine_category}' is already added to your center.")
            return redirect("add_vaccines")

        # Create the vaccine entry
        Vaccines.objects.create(
            center=center,
            vaccine_category=vaccine_category,
            vaccine_name=vaccine_name,
            vaccine_details=vaccine_details,
            doses=doses,
            availability=availability
        )

        messages.success(request, "Vaccine added successfully!")
        return redirect("add_vaccines")

    return render(request, "centers/addvaccines.html", {
        "center_name": center.center_name,  # Read-only center name
        "vaccines": vaccines,
    })


@center_required
def completed_users_view(request):
    """Fetch and display only completed vaccination bookings for the logged-in center."""
    
    center_id = request.session.get('center_id')  # Get logged-in center ID

    try:
        logged_in_center = Healthcenters.objects.get(center_id=center_id)  # Fetch center details
    except Healthcenters.DoesNotExist:
        return redirect('center_login')  # Redirect if center is not found

    # Filter bookings for this specific center with status "completed"
    completed_bookings = BookingDetails.objects.filter(
        center=logged_in_center,
        status="completed"
    )

    return render(request, 'centers/completed_user.html', {'completed_bookings': completed_bookings})
def display_vaccines(request):
    # Ensure the user is logged in and session is set
    center_id = request.session.get("center_id")

    if not center_id:
        messages.error(request, "You must be logged in as a center to access this page.")
        return redirect("center_login")  # Redirect to login if session is missing

    # Fetch the center object based on center_id
    center = Healthcenters.objects.filter(center_id=center_id).first()

    if not center:
        messages.error(request, "Invalid center. Please log in again.")
        return redirect("center_login")

    # Fetch vaccines that belong to the logged-in center using ForeignKey
    vaccines = Vaccines.objects.filter(center=center)

    if not vaccines.exists():
        messages.info(request, "No vaccines have been added by this center yet.")

    return render(request, "centers/viewvaccines.html", {"vaccines": vaccines})

def edit_vaccine(request, id):
    # Get the vaccine instance
    vaccine = get_object_or_404(Vaccines, id=id)

    # Fetch all vaccines for the dropdown
    vaccines = Vaccines.objects.filter(center=vaccine.center)

    if request.method == 'POST':
        # Check if a different vaccine is selected
        selected_vaccine_id = request.POST.get('vaccine_id')
        if selected_vaccine_id and selected_vaccine_id != str(vaccine.id):
            return redirect('edit_vaccine', id=selected_vaccine_id)

        # Update vaccine details
        vaccine.vaccine_category = request.POST.get('vaccine_category')
        vaccine.vaccine_details = request.POST.get('vaccine_details')
        vaccine.availability = request.POST.get('availability') == "True"

        try:
            vaccine.doses = int(request.POST.get('doses', 1))
            vaccine.second_dose_interval = int(request.POST.get('second_dose_interval', 0))
        except ValueError:
            messages.error(request, "Invalid input for doses or second dose interval.")
            return redirect('edit_vaccine', id=id)

        vaccine.save()
        messages.success(request, 'Vaccine updated successfully!')
        return redirect('display_vaccines')

    return render(request, 'centers/editvaccine.html', {'vaccine': vaccine, 'vaccines': vaccines, 'center_name': vaccine.center.center_name})

def delete_vaccine(request, id):
    vaccine = get_object_or_404(Vaccines, id=id)
    vaccine.delete()

    messages.success(request, 'Vaccine deleted successfully!')
    return redirect('display_vaccines')  # Redirect back to vaccine list


def update_center_holidays(request):
    """Allows the logged-in center to update holiday dates."""
    
    # Retrieve the assigned center from session
    center_id = request.session.get("center_id")

    if not center_id:
        messages.error(request, "No center assigned in session.")
        return redirect("center_home")

    center = Healthcenters.objects.filter(center_id=center_id).first()

    if not center:
        messages.error(request, 'Invalid center. Please log in again.')
        return redirect('center_login')  # Redirect to login if center is not found

    if request.method == "POST":
        holiday_dates = request.POST.getlist("holiday_dates")  # Get multiple selected dates

        if holiday_dates:
            for date in holiday_dates:
                CenterHoliday.objects.create(center=center, date=date)

            messages.success(request, "Holidays updated successfully.")
        else:
            messages.error(request, "Please select at least one date.")

        return redirect("view_holidays")  # Reload the page after submission

    # Fetch existing holidays for the logged-in center
    holidays = CenterHoliday.objects.filter(center=center).order_by("date")

    return render(request, "centers/center_holidays.html", {"center": center, "holidays": holidays})

def view_holidays(request):
    # Debugging: Check what is stored in the session
    print("Session center_id:", request.session.get("center_id"))

    center_id = request.session.get("center_id")

    if not center_id:
        messages.error(request, "No center assigned in session. Please log in again.")
        return redirect("center_login")

    center = Healthcenters.objects.filter(center_id=center_id).first()

    if not center:
        messages.error(request, 'Invalid center. Please log in again.')
        return redirect('center_login')  # Redirect to login if center is not found

    # Get holidays for the logged-in center
    holidays = CenterHoliday.objects.filter(center=center).order_by("date")

    return render(request, "centers/center_holidays.html", {"center": center, "holidays": holidays})

def center_bookings(request):
    center_id = request.session.get("center_id")

    if not center_id:
        messages.error(request, "You must be logged in as a health center to view bookings.")
        return redirect("center_login")  

    # Fetch center
    center = get_object_or_404(Healthcenters, center_id=center_id)  # Ensure correct field

    # Get pending bookings (exclude cancelled & rejected)
    pending_bookings = BookingDetails.objects.filter(
        center=center
    ).exclude(status__in=["completed", "cancelled", "rejected"]).order_by("-date", "-time")

    return render(request, "centers/view_bookings.html", {
        "pending_bookings": pending_bookings,
    })


def update_booking_status(request, booking_id, status):
    # Ensure the center is logged in
    if "center_id" not in request.session:
        messages.error(request, "You must be logged in as a health center to update bookings.")
        return redirect("center_login")

    center_id = request.session["center_id"]
    center = get_object_or_404(Healthcenters, center_id=center_id)
    
    # Get the booking
    booking = get_object_or_404(BookingDetails, id=booking_id, center=center)

    user_email = booking.email  # User's email
    center_email = center.email  # Center's email (sender)

    # ⛔ Prevent marking a cancelled booking as completed
    if booking.status == "cancelled" and status == "completed":
        messages.error(request, "You cannot complete a booking that has been cancelled.")
        return redirect("center_bookings")

    if status == "completed":
        booking.status = "completed"
        booking.save()
        
        subject = "Vaccine Booking Completed"
        message = (
            f"Dear {booking.name},\n\n"
            f"Your vaccine appointment has been successfully completed.\n\n"
            f"Details:\n"
            f"- Center: {center.center_name}\n"
            f"- Vaccine: {booking.vaccine_name}\n"
            f"- Date: {booking.date.strftime('%d-%m-%Y')}\n"
            f"- Time: {booking.time.strftime('%I:%M %p')}\n\n"
            f"You can download your vaccination certificate from your profile.\n\n"
            f"Thank you,\n{center.center_name}"
        )

        # ✅ Send email from the center's email
        try:
            send_mail(subject, message, center_email, [user_email], fail_silently=False)
            messages.success(request, "Booking marked as completed and email sent to the user.")
        except Exception as e:
            messages.error(request, f"Booking completed, but email failed: {e}")

        # return generate_vaccine_certificate(request, booking.id)  # Generate certificate

    elif status == "rejected":
        if booking.user:
            Notification.objects.create(
                health_center=center,
                user=booking.user,
                message=f"Your vaccine booking on {booking.date} has been rejected."
            )

        subject = "Vaccine Booking Rejected"
        message = (
            f"Dear {booking.name},\n\n"
            f"We regret to inform you that your vaccine booking has been rejected.\n\n"
            f"Details:\n"
            f"- Center: {center.center_name}\n"
            f"- Vaccine: {booking.vaccine_name}\n"
            f"- Date: {booking.date.strftime('%d-%m-%Y')}\n"
            f"- Time: {booking.time.strftime('%I:%M %p')}\n\n"
            f"For further details, please contact the center at {center.phone}.\n\n"
            f"Thank you,\n{center.center_name}"
        )

        # ✅ Send rejection email from the center's email
        try:
            send_mail(subject, message, center_email, [user_email], fail_silently=False)
            messages.success(request, "Booking rejected and email sent to the user.")
        except Exception as e:
            messages.error(request, f"Booking rejected, but email failed: {e}")

        booking.delete()  # 🔥 Delete the booking on rejection
        messages.info(request, f"Booking for {booking.name} has been rejected and removed.")

    return redirect("center_bookings")  # Redirect back to the bookings page
@center_required
def cancelled_users(request):
    center_id = request.session.get('center_id')  # Get logged-in center ID

    try:
        logged_in_center = Healthcenters.objects.get(center_id=center_id)  # Fetch center details
    except Healthcenters.DoesNotExist:
        return redirect('center_login')  # Redirect if center is not found

    # Filter bookings for this specific center with status "completed"
    cancelled_bookings = BookingDetails.objects.filter(
        center=logged_in_center,
        status="cancelled"
    )
    return render(request, 'centers/cancelled_users.html', {'cancelled_bookings': cancelled_bookings})
    

# def generate_vaccine_certificate(request, booking_id):
#     if "center_id" not in request.session:
#         messages.error(request, "You must be logged in as a center to generate the certificate.")
#         return redirect("center_login")

#     center_id = request.session["center_id"]
#     center = get_object_or_404(Healthcenters, center_id=center_id)
#     booking = get_object_or_404(BookingDetails, id=booking_id, center=center)

#     if booking.center != center:
#         messages.error(request, "You are not authorized to generate this certificate.")
#         return redirect("center_home")

#     user = booking.user

#     # Pass the base URL
#     base_url = f"{request.scheme}://{request.get_host()}"

#     context = {
#         "user": user,
#         "booking": booking,
#         "name": booking.name,
#         "age": booking.age,
#         "date": booking.date.strftime("%Y-%m-%d"),
#         "time": booking.time.strftime("%I:%M %p"),
#         "contact": booking.phone,  # No `contact` field in `BookingDetails`, so use `phone`
#         "place": booking.center.thaluk,  # Fixing the error
#         "vaccine_name": booking.vaccine_name,
#         "center_name": center.center_name,
#         "base_url": base_url,
#     }


#     html_string = render_to_string("centers/certificate_template.html", context)

#     # Ensure `wkhtmltopdf` allows access to local static files
#     options = {
#         "enable-local-file-access": "",
#         "no-stop-slow-scripts": None,
#         "quiet": "",
#     }

#     try:
#         pdf = pdfkit.from_string(html_string, False, configuration=PDFKIT_CONFIG, options=options)
#     except Exception as e:
#         messages.error(request, f"Error generating PDF: {e}")
#         return redirect("center_home")

#     notification = Notification.objects.create(
#         health_center=center,
#         user=user if user else None,
#         message="Your vaccine procedure is now completed.You can download your Vaccine Certificate Down below.",
#     )

#     pdf_filename = f"certificate_{booking.id}.pdf"
#     notification.document.save(pdf_filename, ContentFile(pdf), save=True)

#     response = HttpResponse(pdf, content_type="application/pdf")
#     response["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'

#     messages.success(request, f"Booking completed! Vaccine certificate for {booking.name} has been generated.")

#     return response