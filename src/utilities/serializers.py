from rest_framework import serializers


class ErrorDetailSerializer(serializers.ListSerializer):
    child = serializers.CharField()


class MessageErrorsSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)
    validation_errors = serializers.DictField(
        child=ErrorDetailSerializer(), read_only=True
    )

    class Meta:
        ref_name = "MessageErrors"
