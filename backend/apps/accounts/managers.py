"""Custom user managers for LinkMe accounts."""

from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import validate_username


class UserManager(BaseUserManager):
    """Manager that creates users with email and/or phone."""

    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        phone_number = extra_fields.get("phone_number")
        if not email and not phone_number:
            raise ValueError(_("Email address or phone number is required."))
        if not username:
            raise ValueError(_("Username is required."))

        if email:
            email = self.normalize_email(email).lower()
        else:
            email = None
        username = validate_username(username)

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        try:
            from apps.accounts.bloom import get_username_bloom

            get_username_bloom().add_username(username)
        except Exception:
            # Bloom is an optimization; DB uniqueness remains authoritative.
            pass
        return user

    def create_user(self, email=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_verified", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        if not email:
            raise ValueError(_("Superuser must have an email address."))

        return self._create_user(email, username, password, **extra_fields)
