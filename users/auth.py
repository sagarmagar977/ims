from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Accepts:
    - email + password
    """

    email = serializers.EmailField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide username from request schema and enforce email-only login payload.
        self.fields.pop(self.username_field, None)

    def validate(self, attrs):
        attrs = dict(attrs)
        email = (attrs.get("email") or "").strip()
        password = attrs.get("password")

        if not password:
            raise serializers.ValidationError({"password": "This field is required."})

        if not email:
            raise serializers.ValidationError({"email": "This field is required."})

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            # Keep message aligned with auth failure semantics.
            raise serializers.ValidationError({"detail": "No active account found with the given credentials"})
        attrs[self.username_field] = user.get_username()

        return super().validate(attrs)


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer
