# this will describe the process of going from a python object to json

from rest_framework import serializers
from .models import Drink
from .models import AdvanceStats

class DrinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drink
        fields = ['id', 'name', 'description']

class AdvanceStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvanceStats
        fields = '__all__'