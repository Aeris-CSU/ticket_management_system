from rest_framework import serializers

from .models import Technicians
class TechniciansSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technicians
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'write_only': True,
            }
        }

    def create(self, validated_data):
        password = validated_data.pop('password')

        technician = Technicians.objects.create(**validated_data)
        technician.set_password(password)
        technician.save()
        return technician

    def update(self, instance, validated_data):
        password = validated_data.pop('password')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance