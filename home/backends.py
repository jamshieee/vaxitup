from django.contrib.auth.backends import BaseBackend
from .models import Hlthcenters

class CenterAuthenticationBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find the center by username
            center = Hlthcenters.objects.get(username=username)
            # Check if the password matches
            if center.password == password:
                return center  # Return the authenticated center object
            else:
                return None  # Invalid password
        except Hlthcenters.DoesNotExist:
            return None  # Center does not exist

    def get_user(self, user_id):
        try:
            return Hlthcenters.objects.get(pk=user_id)
        except Hlthcenters.DoesNotExist:
            return None
