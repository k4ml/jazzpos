from rest_framework import serializers

from xpos.models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
