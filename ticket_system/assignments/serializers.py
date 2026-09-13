from rest_framework import serializers
from assignments.models import Assignments

class AssignmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignments
        fields = '__all__'

