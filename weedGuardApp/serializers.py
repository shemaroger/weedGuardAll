from rest_framework import serializers
from .models import *
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    # Set the default value of the role field to 'farmer'
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='farmer')

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'role']

    def create(self, validated_data):
        # Ensure that role is set to 'farmer' if not provided
        role = validated_data.get('role', 'farmer')  # Default to 'farmer' if not provided
        user = User.objects.create(
            fullname=validated_data['fullname'],
            email=validated_data['email'],
            role=role
        )
        user.password = make_password(validated_data['password'])  # Hash the password
        user.save()
        return user

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(read_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive.")
        data['role'] = user.role
        data['user'] = user
        return data


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ['id', 'image', 'result', 'location', 'site_name', 'timestamp', 'user']
class PredictionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ['id', 'result', 'timestamp', 'location', 'site_name']