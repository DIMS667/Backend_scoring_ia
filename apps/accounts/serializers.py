from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, ClientProfile

class ClientProfileSerializer(serializers.ModelSerializer):
    debt_ratio = serializers.ReadOnlyField()
    
    class Meta:
        model = ClientProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    client_profile = ClientProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'client_profile', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'phone', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Créer profil client si rôle CLIENT
        if user.role == 'CLIENT':
            ClientProfile.objects.create(
                user=user,
                cni_number='',
                birth_date='2000-01-01',
                birth_place='',
                employment_status='EMPLOYEE',
                monthly_income=0,
                address=''
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)