from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class UserRoles(models.TextChoices):
        SELLER = 's', "SELLER"
        SUPERADMIN = 'sa', "SUPERADMIN"
        ADMIN = 'a', "ADMIN"

    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=10, choices=UserRoles.choices, default=UserRoles.SELLER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.full_name or self.username


class RequestLog(models.Model):
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='request_logs')
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.PositiveSmallIntegerField()
    duration_ms = models.PositiveIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'request_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['method']),
            models.Index(fields=['status_code']),
        ]

    def __str__(self):
        user_str = str(self.user) if self.user else 'anonymous'
        return f"{self.method} {self.path} [{self.status_code}] by {user_str}"
