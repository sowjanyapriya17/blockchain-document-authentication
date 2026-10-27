from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Profile


def role_required(*allowed_roles):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            profile = Profile.objects.filter(
                user=request.user
            ).first()

            if profile is None:
                raise PermissionDenied(
                    "Your user profile does not exist."
                )

            if not profile.is_approved:
                raise PermissionDenied(
                    "Your account is waiting for adminstartor approval."
                )

            if profile.role not in allowed_roles:
                raise PermissionDenied(
                    "You do not have permission to access this page."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator