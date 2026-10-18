from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import Authentication, OTPVerification, LoginAttempt, Notification
from authentication.serializers import AuthenticationSerializer, NotificationSerializer
from customers.models import Customers
from .permissions import *


class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        if not username or not password:
            return Response(
                {'error': 'username or password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        MAX_ATTEMPTS = 3
        LOCKOUT_MINUTES = 15
        cutoff_time = timezone.now() - timedelta(minutes=LOCKOUT_MINUTES)

        recent_successful = (
            LoginAttempt.objects.filter(username=username, successful=True)
            .order_by('-timestamp')
            .first()
        )
        if recent_successful and recent_successful.timestamp > cutoff_time:
            cutoff_time = recent_successful.timestamp

        failed_attempts = LoginAttempt.objects.filter(
            username=username,
            successful=False,
            timestamp__gte=cutoff_time
        ).count()

        if failed_attempts >= MAX_ATTEMPTS:
            print(f"\n[ACCOUNT LOCKED] Username: '{username}' has reached maximum failed attempts ({MAX_ATTEMPTS}).\n")
            return Response(
                data={
                    'message': f'Account locked due to {MAX_ATTEMPTS} failed attempts. Please try again after {LOCKOUT_MINUTES} minutes or reset your password via OTP.'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        account = authenticate(username=username, password=password)

        if account is None:
            LoginAttempt.objects.create(username=username, ip_address=ip, successful=False)
            current_failed = failed_attempts + 1
            remaining_attempts = max(0, MAX_ATTEMPTS - current_failed)

            print(f"\n[LOGIN FAILED] Username: '{username}' | Attempt: {current_failed}/{MAX_ATTEMPTS} | Remaining: {remaining_attempts} | IP: {ip}\n")

            if remaining_attempts == 0:
                msg = f'Invalid credentials. Account is now locked for {LOCKOUT_MINUTES} minutes.'
            else:
                msg = f'Username or password is incorrect. {remaining_attempts} attempt(s) remaining.'

            return Response(
                data={
                    'message': msg,
                    'failed_attempts': current_failed,
                    'remaining_attempts': remaining_attempts
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        LoginAttempt.objects.create(username=username, ip_address=ip, successful=True)
        print(f"\n[LOGIN SUCCESS] User: '{account.username}' (Role: {account.role}) | IP: {ip}\n")

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


class AdminRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AuthenticationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminList(APIView):
    permission_classes = [AdminPermission]

    def get(self, request):
        accounts = Authentication.objects.filter(role=Authentication.ROLE_CHOICES.ADMIN)
        serializer = AuthenticationSerializer(accounts, many=True)
        return Response(serializer.data)


class AccountList(APIView):
    permission_classes = [AdminPermission]

    def get(self, request):
        accounts = Authentication.objects.all()
        serializer = AuthenticationSerializer(accounts, many=True)
        return Response(serializer.data)


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        purpose = request.data.get('purpose')

        if not email or not purpose:
            return Response(
                {'message': 'Email and purpose are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if purpose == 'RESET_PASSWORD':
            if not Authentication.objects.filter(email=email).exists():
                return Response(
                    {'message': 'No account registered with this email.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif purpose == 'REGISTER':
            if Authentication.objects.filter(email=email).exists():
                return Response(
                    {'message': 'An account already exists with this email.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        otp_code = OTPVerification.generate_otp()
        OTPVerification.objects.create(email=email, otp_code=otp_code, purpose=purpose)

        print("\n" + "=" * 42)
        print(f" OTP for {email} ({purpose}): {otp_code} ")
        print("=" * 42 + "\n")

        try:
            send_mail(
                subject='Your Helpdesk Verification Code',
                message=f'Your 6-digit OTP verification code is: {otp_code}. It will expire in 10 minutes.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@helpdesk.com'),
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error note: {e}")

        return Response(
            {'message': f'OTP sent successfully to {email}.'},
            status=status.HTTP_200_OK
        )


class VerifyOTPAndRegisterCustomerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        otp_code = request.data.get('otp_code', '').strip()
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        address = request.data.get('address', 'Not specified')

        if not all([email, otp_code, username, password]):
            return Response(
                {'message': 'Username, password, email, and OTP code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_record = OTPVerification.objects.filter(
            email=email,
            purpose='REGISTER',
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_record or otp_record.is_expired():
            return Response(
                {'message': 'OTP has expired or no request was found. Please request a new OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_record.has_exceeded_attempts():
            return Response(
                {'message': 'Maximum OTP attempts exceeded. Please request a new OTP.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if otp_record.otp_code != otp_code:
            otp_record.attempts += 1
            otp_record.save()
            remaining = max(0, OTPVerification.MAX_ATTEMPTS - otp_record.attempts)
            print(f"\n[OTP VERIFICATION FAILED] {email} (REGISTER) | Attempt {otp_record.attempts}/{OTPVerification.MAX_ATTEMPTS} | Remaining: {remaining}\n")

            if remaining == 0:
                msg = 'Incorrect OTP code. Maximum attempts reached. Please request a new OTP.'
            else:
                msg = f'Incorrect OTP code. {remaining} attempt(s) remaining.'

            return Response({'message': msg, 'remaining_attempts': remaining}, status=status.HTTP_400_BAD_REQUEST)

        if Authentication.objects.filter(username=username).exists():
            return Response(
                {'message': 'Username is already taken.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_record.is_verified = True
        otp_record.save()

        user = Authentication.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=Authentication.ROLE_CHOICES.CUSTOMER
        )
        Customers.objects.create(user=user, address=address)

        # Notify administrators about new registration
        admin_users = Authentication.objects.filter(role=Authentication.ROLE_CHOICES.ADMIN)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                title="New Customer Registered",
                message=f"Customer {user.first_name} {user.last_name} (@{user.username}) registered."
            )

        return Response(
            {'message': 'Customer registered and verified successfully.'},
            status=status.HTTP_201_CREATED
        )


class VerifyOTPAndResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        otp_code = request.data.get('otp_code', '').strip()
        new_password = request.data.get('new_password', '')

        if not all([email, otp_code, new_password]):
            return Response(
                {'message': 'Email, OTP code, and new password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_record = OTPVerification.objects.filter(
            email=email,
            purpose='RESET_PASSWORD',
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_record or otp_record.is_expired():
            return Response(
                {'message': 'OTP has expired or no request was found. Please request a new OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_record.has_exceeded_attempts():
            return Response(
                {'message': 'Maximum OTP attempts exceeded. Please request a new OTP.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if otp_record.otp_code != otp_code:
            otp_record.attempts += 1
            otp_record.save()
            remaining = max(0, OTPVerification.MAX_ATTEMPTS - otp_record.attempts)
            print(f"\n[OTP VERIFICATION FAILED] {email} (RESET_PASSWORD) | Attempt {otp_record.attempts}/{OTPVerification.MAX_ATTEMPTS} | Remaining: {remaining}\n")

            if remaining == 0:
                msg = 'Incorrect OTP code. Maximum attempts reached. Please request a new OTP.'
            else:
                msg = f'Incorrect OTP code. {remaining} attempt(s) remaining.'

            return Response({'message': msg, 'remaining_attempts': remaining}, status=status.HTTP_400_BAD_REQUEST)

        user = Authentication.objects.filter(email=email).first()
        if not user:
            return Response(
                {'message': 'No account found with this email.'},
                status=status.HTTP_404_NOT_FOUND
            )

        otp_record.is_verified = True
        otp_record.save()

        user.set_password(new_password)
        user.save()

        LoginAttempt.objects.filter(username=user.username, successful=False).delete()
        print(f"\n[LOCKOUT CLEARED] Failed login attempts reset for user: '{user.username}' after OTP password recovery.\n")

        Notification.objects.create(
            user=user,
            title="Password Changed",
            message="Your account password was successfully reset."
        )

        return Response(
            {'message': 'Password has been reset successfully. Your account is unlocked.'},
            status=status.HTTP_200_OK
        )


# ==========================================
# Notification Endpoints
# ==========================================
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)