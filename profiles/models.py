from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.validators import RegexValidator
from django.core.files.base import File
from PIL import Image
from io import BytesIO


class CustomUserManager(BaseUserManager):
    """Custom manager for user authentication using email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with elevated permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        """Allow authentication using email instead of username."""
        return self.get(email=email)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True, blank=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$", message="Enter a valid phone number."
            )
        ],
    )
    date_of_birth = models.DateField(null=True, blank=True)  # New Field

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="user_profiles",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="user_profiles_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def process_image(self, image_file):
        """Optimize image size and quality before saving."""
        try:
            img = Image.open(image_file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            MAX_WIDTH, MAX_HEIGHT = 735, 724
            ratio = min(MAX_WIDTH / img.width, MAX_HEIGHT / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))

            img = img.resize(new_size, Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            output.seek(0)

            return File(output, name=f"profile_{self.pk}.jpg")

        except Exception as e:
            print(f"Error processing image: {e}")
            return image_file

    def save(self, *args, **kwargs):
        """Ensure username uniqueness and optimize profile images."""
        if not self.username:
            base_username = self.email.split("@")[0]
            username = base_username
            counter = 1

            while UserProfile.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            self.username = username

        if self.profile_pic:
            self.profile_pic = self.process_image(self.profile_pic)

        super().save(*args, **kwargs)

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name (first name) of the user."""
        return self.first_name

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
