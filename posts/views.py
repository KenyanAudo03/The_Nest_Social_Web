from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Media
from .forms import PostForm, MediaUploadForm
from django.forms import modelformset_factory
from django.contrib.auth import authenticate, login as auth_login
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.urls import reverse


# Create your views here.

# Login
@never_cache
def user_login(request):
    if request.method == "POST":
        email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if not user.email_verified:
                messages.error(
                request,
                mark_safe(f'Email not verified. <a href="{reverse("resend_email", args=[email])}">Click here</a> to verify.')
                )
                return render(request, "login.html")

            auth_login(request, user)
            return redirect("posts:home")
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "login.html")

    csrf_token = get_token(request)
    response = render(request, "login.html", {"csrf_token": csrf_token})
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response

def home(request):
    if not request.user.is_authenticated:
        return redirect("user_login")  # Redirects to the login page
    
    posts = (
        Post.objects.select_related("user")
        .prefetch_related("media")
        .order_by("-created_at")
    )
    return render(request, "home.html", {"posts": posts})

@login_required
def create_post(request):
    if request.method == "POST":
        post_form = PostForm(request.POST)
        media_form = MediaUploadForm(request.POST, request.FILES)

        if post_form.is_valid() and media_form.is_valid():
            post = post_form.save(commit=False)
            post.user = request.user
            post.save()

            # Handle multiple file uploads
            files = request.FILES.getlist("files")
            for file in files:
                # Optional: Add file type validation here
                Media.objects.create(post=post, file=file)

            return redirect("posts:home")  # Removed pk parameter since it wasn't needed
    else:
        post_form = PostForm()
        media_form = MediaUploadForm()

    return render(
        request,
        "create_post.html",
        {"post_form": post_form, "media_form": media_form},
    )
