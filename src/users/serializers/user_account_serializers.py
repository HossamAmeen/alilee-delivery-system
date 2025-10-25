from rest_framework import serializers

from users.models import UserAccount


class UserAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserAccount
        fields = ['id', 'email', 'password', 'full_name', 'phone_number', 'role', 'created', 'modified']
        read_only_fields = ('id', 'created', 'modified')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
