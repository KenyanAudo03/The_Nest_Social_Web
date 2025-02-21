from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Media, Like
from .forms import PostForm, MediaUploadForm
from django.forms import modelformset_factory
from django.contrib.auth import authenticate, login as auth_login
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta
from django.http import JsonResponse
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Exists, OuterRef

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
                    mark_safe(
                        f'Email not verified. <a href="{reverse("resend_email", args=[email])}">Click here</a> to verify.'
                    ),
                )
                return render(request, "login.html")

            auth_login(request, user)
            return redirect("home")
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
    FREE_ACCESS_DURATION = timedelta(minutes=1)

    # If the user is authenticated, allow access
    if request.user.is_authenticated:
        posts = (
            Post.objects.select_related("user")
            .prefetch_related("media")
            .annotate(
                like_count=Count("likes"), 
                is_liked=Exists(
                    Like.objects.filter(user=request.user, post=OuterRef("pk"))
                ), 
            )
            .order_by("-created_at")
        )

        return render(request, "home.html", {"posts": posts})
    first_visit = request.session.get("guest_first_visit")

    if not first_visit:
        request.session["guest_first_visit"] = now().isoformat()
    else:
        first_visit_time = now().fromisoformat(first_visit)
        if now() - first_visit_time > FREE_ACCESS_DURATION:
            messages.warning(
                request, "Your guest access has expired. Please log in to continue."
            )
            return redirect("user_login")

    posts = (
        Post.objects.select_related("user")
        .prefetch_related("media")
        .annotate(like_count=Count("likes"))
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

            return redirect("posts:home")
    else:
        post_form = PostForm()
        media_form = MediaUploadForm()

    return render(
        request,
        "create_post.html",
        {"post_form": post_form, "media_form": media_form},
    )


@login_required
def toggle_like(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if created:
            is_liked = True
        else:
            is_liked = False
            like.delete()

        # Refresh the like count after modification
        post.refresh_from_db()
        like_count = post.likes.count()

        return JsonResponse({"is_liked": is_liked, "like_count": like_count})

    return JsonResponse({"error": "Invalid request"}, status=400)
