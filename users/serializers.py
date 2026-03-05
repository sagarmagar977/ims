from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "full_name_nepali",
            "email",
            "role",
            "office",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password is not None or confirm_password is not None:
            if not password:
                raise serializers.ValidationError({"password": "Password is required when confirm_password is provided."})
            if not confirm_password:
                raise serializers.ValidationError({"confirm_password": "Please confirm the password."})
            if password != confirm_password:
                raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff and request.user.pk == instance.pk:
            protected_fields = ("role", "office", "is_active")
            changed_protected = [field for field in protected_fields if field in validated_data]
            if changed_protected:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "You cannot update privileged account fields "
                            "(role, office, is_active) on your own profile."
                        )
                    }
                )

        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
