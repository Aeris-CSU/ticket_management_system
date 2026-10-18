from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers import AuthenticationSerializer
from .models import Authentication
from .permissions import AdminPermission, TechnicianPermission
from django.db import transaction
from .serializers import ChangePasswordSerializer


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

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


class DeleteOwnAccount(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        from django.db.models.deletion import ProtectedError
        from customers.views import delete_customer_account
        from technicians.views import delete_technician_account
        from customers.models import Customers
        from technicians.models import Technicians
        with transaction.atomic():
            user = Authentication.objects.select_for_update().get(pk=request.user.pk)
            if user.role not in ('CUSTOMER', 'TECHNICIAN'):
                return Response({'detail': 'Only customers and technicians can delete their own accounts.'}, status=status.HTTP_403_FORBIDDEN)
            model = Customers if user.role == 'CUSTOMER' else Technicians
            profile = model.objects.filter(user=user).first()
            if profile:
                return delete_customer_account(profile) if user.role == 'CUSTOMER' else delete_technician_account(profile)
            try:
                with transaction.atomic():
                    user.delete()
            except ProtectedError:
                return Response({'detail': 'Your account has protected history and cannot be deleted.'}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwnProfilePicture(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        from .serializers import ProfilePictureSerializer
        serializer = ProfilePictureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.profile_picture = serializer.validated_data['profile_picture']
        user.save(update_fields=['profile_picture', 'updated_at'])
        return Response(AuthenticationSerializer(user).data)

    def delete(self, request):
        user = request.user
        user.profile_picture = ''
        user.save(update_fields=['profile_picture', 'updated_at'])
        return Response(AuthenticationSerializer(user).data)
