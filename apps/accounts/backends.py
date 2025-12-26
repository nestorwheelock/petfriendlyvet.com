"""Custom authentication backends."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Authenticate using email address instead of username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate user by email.

        Args:
            request: The HTTP request.
            username: The email address (form field is named 'username').
            password: The password.

        Returns:
            User if authentication succeeds, None otherwise.
        """
        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if username is None or password is None:
            return None

        try:
            # Try to find user by email
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # Multiple users with same email - use first active one
            user = UserModel.objects.filter(
                email__iexact=username, is_active=True
            ).first()
            if user is None:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
