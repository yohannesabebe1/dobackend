from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField()
    
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'status', 'payment_id', 'course', 'gateway', 'chapa_tx_ref']