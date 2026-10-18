import re
from rest_framework import serializers


def validate_mobile_number(value):
    value = value.strip()
    if not value:
        return value
    compact = re.sub(r'[\s-]', '', value)
    if not re.fullmatch(r'(?:09[0-9]{9}|\+639[0-9]{9})', compact):
        raise serializers.ValidationError('Enter a Philippine mobile number such as 09171234567 or +639171234567.')
    return value
