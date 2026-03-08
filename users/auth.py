from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Accepts either:
    - username + password (existing behavior), or
    - email + password (frontend login form compatibility).
    """

    email = serializers.EmailField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].required = False

    def validate(self, attrs):
        attrs = dict(attrs)
        email = (attrs.get("email") or "").strip()
        username = (attrs.get("username") or "").strip()
        password = attrs.get("password")

        if not password:
            raise serializers.ValidationError({"password": "This field is required."})

        if email and not username:
            User = get_user_model()
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                # Keep message aligned with auth failure semantics.
                raise serializers.ValidationError({"detail": "No active account found with the given credentials"})
            attrs[self.username_field] = user.get_username()
        elif not username:
            raise serializers.ValidationError({"username": "Provide either username or email."})

        return super().validate(attrs)


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer
