from rest_framework import serializers
from .models import CustomUser, Project
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "Password didn't match."
                )
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError(
                "Email and password are required."
                )
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                "Invalid email or password."
                )
        data['user'] = user
        return data


class ProjectSerializer(serializers.ModelSerializer):
    # manager = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('manager',)
