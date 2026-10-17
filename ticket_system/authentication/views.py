from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers import AuthenticationSerializer
from .models import Authentication
from .permissions import AdminPermission
from django.db import transaction
from .serializers import ChangePasswordSerializer


class ChangePassword(APIView):
    permission_classes = [AdminPermission]

    def post(self, request):
        with transaction.atomic():
            user = Authentication.objects.select_for_update().get(pk=request.user.pk)
            serializer = ChangePasswordSerializer(data=request.data, context={'user': user})
            serializer.is_valid(raise_exception=True)
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password', 'updated_at'])
        return Response({'detail': 'Password updated. Please sign in again.'})

class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'detail': 'username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        account = authenticate(username=username, password=password)

        if account is None:
            return Response(
                data={'detail': 'Username or password is incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(account)

        serializer = AuthenticationSerializer(account)

        return Response(
            data={
                'message': 'Successfully logged in',
                'account': serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            },
            status=status.HTTP_200_OK
        )
class AdminList(APIView):
    permission_classes = [AdminPermission]
    def get(self, request):
        accounts = Authentication.objects.filter(role=Authentication.ROLE_CHOICES.ADMIN)
        serializer = AuthenticationSerializer(accounts, many=True)
        return Response(serializer.data)

class AccountList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user.role == Authentication.ROLE_CHOICES.ADMIN:
            accounts = Authentication.objects.all().order_by('id')
            serializer = AuthenticationSerializer(accounts, many=True)
            return Response(serializer.data)

        serializer = AuthenticationSerializer(request.user)
        return Response(serializer.data)
