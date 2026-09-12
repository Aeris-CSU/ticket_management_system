from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.status import HTTP_201_CREATED
from rest_framework.permissions import AllowAny

from technicians.models import Technicians
from technicians.serializers import TechniciansSerializer, TechnicianListSerializer
from authentication.models import Authentication


class TechnicianLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'username or password is required'}, status=status.HTTP_400_BAD_REQUEST)

        account = authenticate(username=username, password=password)
        if account is None:
            return Response(
                data={'message': 'Username and Password are not valid'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Fetch the Technicians profile linked to this Authentication user
        try:
            technician_profile = Technicians.objects.get(user=account)
        except Technicians.DoesNotExist:
            return Response(
                data={'message': 'Technician profile not found for this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        refresh = RefreshToken.for_user(account)

        # Serialize the technician profile instance instead of the base account user
        serializer = TechniciansSerializer(technician_profile)

        return Response(
            data={
                'message': 'Login Successful',
                'account': serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            },
            status=status.HTTP_200_OK
        )


class TechnicianRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TechniciansSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TechnicianView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        technicians = Technicians.objects.select_related('user').all()
        serializer = TechnicianListSerializer(technicians, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)