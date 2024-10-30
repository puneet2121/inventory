from rest_framework import serializers
from .models import Barcode, Product


class BarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barcode
        fields = ['id', 'code', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    barcode = BarcodeSerializer()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'barcode']
