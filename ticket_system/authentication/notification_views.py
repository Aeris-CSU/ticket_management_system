from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification


class NotificationActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['read', 'delete'])
    all = serializers.BooleanField(default=False)
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, max_length=100)

    def validate(self, attrs):
        if not attrs.get('all') and not attrs.get('ids'):
            raise serializers.ValidationError('Select notifications or explicitly choose all.')
        return attrs


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = Notification.objects.filter(recipient=request.user)
        unread = query.filter(is_read=False).count()
        if request.query_params.get('filter') == 'unread':
            query = query.filter(is_read=False)
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            return Response({'detail': 'Invalid page.'}, status=400)
        total = query.count()
        rows = query.select_related('ticket__customer').prefetch_related('ticket__assignments_set__technicians').all()[(page-1)*30:page*30]
        data = []
        for item in rows:
            ticket = item.ticket
            can_open = bool(ticket and not ticket.deleted_at)
            if can_open and request.user.role == 'CUSTOMER':
                can_open = ticket.customer.user_id == request.user.pk
            elif can_open and request.user.role == 'TECHNICIAN':
                can_open = any(a.is_active and a.technicians.user_id == request.user.pk for a in ticket.assignments_set.all())
            data.append({'id': item.pk, 'message': item.message, 'event': item.event, 'is_read': item.is_read, 'created_at': item.created_at, 'ticket_id': item.ticket_id if can_open else None})
        return Response({'results': data, 'unread_count': unread, 'total': total, 'has_more': page*30 < total})

    def post(self, request):
        serializer = NotificationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        query = Notification.objects.filter(recipient=request.user)
        if not values['all']:
            query = query.filter(pk__in=values['ids'])
        if values['action'] == 'read':
            count = query.update(is_read=True)
        else:
            count, _ = query.delete()
        return Response({'affected': count})
