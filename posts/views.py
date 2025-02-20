from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Media
from .forms import PostForm, MediaUploadForm
from django.forms import modelformset_factory


# Create your views here.
def home(request):
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
