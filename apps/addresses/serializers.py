from rest_framework import serializers
from .models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "user", "street", "city", "state",
            "zip_code", "country", "is_default", "created_at"
        ]
        read_only_fields = ["id", "created_at", "user"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)
