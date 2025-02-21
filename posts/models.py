from django.db import models
from django.conf import settings


class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    content = models.TextField(blank=True, null=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    reposted_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reposted_posts",
    )
    repost_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Post by {self.user.username} - {self.created_at}"

    def increment_repost_count(self):
        """Increment repost count for the original post"""
        if self.reposted_from:
            self.reposted_from.repost_count += 1
            self.reposted_from.save()


class Media(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="posts/media/")

    def __str__(self):
        return f"Media for Post ID {self.post.id}"


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")  # Ensure a user can like a post only once

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"


class View(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="views",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="views")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View on Post {self.post.id}"
