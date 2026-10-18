from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from authentication.models import Authentication


class ProfilePictureTests(APITestCase):
    def picture(self):
        data = BytesIO()
        Image.new('RGB', (30, 30), 'blue').save(data, 'PNG')
        return SimpleUploadedFile('photo.png', data.getvalue(), content_type='image/png')

    def test_all_roles_upload_and_remove_only_their_own_picture(self):
        with TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            other = Authentication.objects.create_user(username='other-picture', role='CUSTOMER')
            for role in ('ADMIN', 'TECHNICIAN', 'CUSTOMER'):
                user = Authentication.objects.create_user(username=role, role=role)
                self.client.force_authenticate(user)
                response = self.client.put('/api/accounts/me/picture/', {'profile_picture': self.picture(), 'user_id': other.pk}, format='multipart')
                self.assertEqual(response.status_code, 200)
                self.assertIn('/media/profile_pictures/', response.data['profile_picture'])
                user.refresh_from_db()
                self.assertTrue(user.profile_picture.name.endswith('.jpg'))
                self.assertEqual(self.client.get('/api/accounts/').status_code, 200)
                other.refresh_from_db()
                self.assertFalse(other.profile_picture)
                self.assertEqual(self.client.delete('/api/accounts/me/picture/').status_code, 200)
                user.refresh_from_db()
                self.assertFalse(user.profile_picture)

    def test_anonymous_and_invalid_uploads_are_rejected(self):
        self.assertEqual(self.client.put('/api/accounts/me/picture/', {}).status_code, 401)
        user = Authentication.objects.create_user(username='bad-picture', role='CUSTOMER')
        self.client.force_authenticate(user)
        fake = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        self.assertEqual(self.client.put('/api/accounts/me/picture/', {'profile_picture': fake}, format='multipart').status_code, 400)
        image = self.picture()
        image.size = 6 * 1024 * 1024
        from authentication.serializers import ProfilePictureSerializer
        serializer = ProfilePictureSerializer(data={'profile_picture': image})
        self.assertFalse(serializer.is_valid())
