from rest_framework import serializers
from .models import Manager


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        fields = '__all__'
        read_only_fields = ('id', 'created', 'modified', 'deleted_at')
