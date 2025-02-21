from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import EmailVerificationToken, PasswordResetToken
from django.utils.crypto import get_random_string
from urllib.parse import urlparse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.urls import reverse
import uuid
from django.http import HttpResponse
from profiles.models import UserProfile
from datetime import datetime
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.utils.timezone import now
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import update_session_auth_hash


# Create your views here.


User = get_user_model()


def check_password_strength(password):
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not any(c.isupper() for c in password):
        errors.append("Include at least one uppercase letter in your password.")
    if not any(c.islower() for c in password):
        errors.append("Include at least one lowercase letter in your password.")
    if not any(c.isdigit() for c in password):
        errors.append("Include at least one number in your password.")

    return errors


def signup(request):
    today = datetime.today()
    current_day = today.day
    current_month = today.month
    current_year = today.year

    days = list(range(1, 32))
    years = list(range(current_year, 1899, -1))
    months = [
        {"num": 1, "name": "Jan"},
        {"num": 2, "name": "Feb"},
        {"num": 3, "name": "Mar"},
        {"num": 4, "name": "Apr"},
        {"num": 5, "name": "May"},
        {"num": 6, "name": "Jun"},
        {"num": 7, "name": "Jul"},
        {"num": 8, "name": "Aug"},
        {"num": 9, "name": "Sep"},
        {"num": 10, "name": "Oct"},
        {"num": 11, "name": "Nov"},
        {"num": 12, "name": "Dec"},
    ]

    if request.method == "POST":
        # Get form data
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        # Handle date components
        day = request.POST.get("day", str(current_day))
        selected_month = int(request.POST.get("month", current_month))
        year = request.POST.get("year", str(current_year))

        # Format date of birth
        dob = (
            f"{year}-{selected_month}-{day}" if all([day, selected_month, year]) else ""
        )

        # Prepare context for potential re-render
        context = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "day": day,
            "month": selected_month,
            "year": year,
            "days": days,
            "months": months,
            "years": years,
            "password": password,
        }

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(
                request, mark_safe('Email already in use. <a href="/">Login here</a>.')
            )
            return render(request, "signup.html", context)

        # Validate password
        password_errors = check_password_strength(password)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return render(request, "signup.html", context)

        # Create user
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            email_verified=False,
            date_of_birth=dob,
        )
        user.set_password(password)
        user.save()

        # Create verification token
        token = EmailVerificationToken.objects.create(
            user=user, token=str(uuid.uuid4())
        )

        # Send verification email
        send_verification_email(request, user, token.token)
        messages.success(
            request, "A verification email has been sent, please verify your account"
        )

        return redirect("email_sent", email=email)

    # GET request - initial form load
    print(current_month)
    context = {
        "first_name": "",
        "last_name": "",
        "email": "",
        "day": str(current_day),
        "month": current_month,
        "year": str(current_year),
        "days": days,
        "months": months,
        "years": years,
    }

    return render(request, "signup.html", context)


def send_verification_email(request, user, token):
    """Sends a verification email with a unique token link."""
    verification_link = request.build_absolute_uri(
        reverse("verify_email", args=[token])
    )

    parsed_url = urlparse(verification_link)
    domain = parsed_url.hostname

    subject = "Verify Your Email"
    html_message = render_to_string(
        "email_verification.html",
        {
            "user": user,
            "verification_link": verification_link,
        },
    )
    plain_message = strip_tags(html_message)

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=f"noreply@{domain}",
        to=[user.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send()


def verify_email(request, token):
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)

        user = verification_token.user
        user.email_verified = True
        user.save()

        verification_token.delete()

        messages.success(request, "Email verified successfully!")
        return redirect("posts:home")

    except EmailVerificationToken.DoesNotExist:
        return HttpResponse("Invalid or expired verification link.", status=400)


def email_sent(request, email):
    user = get_object_or_404(User, email=email)

    if user.email_verified:
        messages.error(request, "You cannot change your email after verification.")
        return redirect("posts:home")

    if request.method == "POST":
        new_email = request.POST.get("email", "").strip()
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            messages.error(request, "This email is already in use.")
            return render(request, "email_sent.html", {"email": email})

        # Update user email
        user.email = new_email
        user.email_verified = False
        user.save()

        # Remove old verification tokens
        EmailVerificationToken.objects.filter(user=user).delete()
        new_token = EmailVerificationToken.objects.create(
            user=user, token=str(uuid.uuid4())
        )
        send_verification_email(request, user, new_token.token)

        messages.success(
            request,
            "Your email has been updated! A new verification email has been sent.",
        )
        return redirect("email_sent", email=new_email)

    return render(request, "email_sent.html", {"email": email})


def resend_email(request, email):
    try:
        user = User.objects.get(email=email)
        if user.email_verified:
            return redirect("posts:home")

        # Generate new token
        token, created = EmailVerificationToken.objects.get_or_create(
            user=user, defaults={"token": str(uuid.uuid4())}
        )
        send_verification_email(request, user, token.token)

        messages.success(request, "A new verification email has been sent.")
        return redirect("email_sent", email=email)

    except User.DoesNotExist:
        return redirect("signup")





# Forgot Password
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email").strip()

        try:
            user = User.objects.get(email=email)
            token = get_random_string(32)

            # Save the token in the database
            PasswordResetToken.objects.create(user=user, token=token)

            # Create the reset URL
            reset_link = request.build_absolute_uri(
                reverse("reset_password", args=[token])
            )

            # Render email template
            html_message = render_to_string(
                "forgot-pass-email.html",
                {
                    "user": user,
                    "reset_link": reset_link,
                },
            )
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject="Password Reset Request",
                message=plain_message,
                from_email="noreply@example.com",
                recipient_list=[user.email],
                html_message=html_message,
            )

            messages.success(request, "A reset link has been sent to your email.")
            return redirect("user_login")

        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("forgot_password")

    return render(request, "forgot_password.html")


# Reset Password
def reset_password(request, token):
    # Check if the token exists
    reset_token = PasswordResetToken.objects.filter(token=token).first()

    if not reset_token:
        messages.error(
            request, "Invalid or expired token. Please request a new password reset."
        )
        return redirect("forgot_password")

    # Check if token has expired (1-hour limit)
    time_elapsed = (now() - reset_token.created_at).total_seconds()
    if time_elapsed > 3600:
        reset_token.delete()
        messages.error(
            request, "Token has expired. Please request a new password reset."
        )
        return redirect("forgot_password")

    if request.method == "POST":
        new_password = request.POST.get("password").strip()
        confirm_password = request.POST.get("confirm_password").strip()

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password", token=token)

        # Update user password
        reset_token.user.set_password(new_password)
        reset_token.user.save()
        update_session_auth_hash(request, reset_token.user)
        reset_token.delete()

        messages.success(
            request, "Your password has been reset successfully. Please log in."
        )
        return redirect("user_login")

    return render(request, "reset_password.html", {"token": token})
