from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny

from authentication.serializers import AuthenticationSerializer


class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'username or password is required'}, status=status.HTTP_400_BAD_REQUEST)

        account = authenticate(username=username, password=password)

        if account is None:
            return Response(
                data={'message': 'Username or password is incorrect'},
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