from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_local_admin(apps, schema_editor):
    Account = apps.get_model('authentication', 'Authentication')
    Account.objects.using(schema_editor.connection.alias).get_or_create(
        username='localadmin',
        defaults={
            'password': make_password('TickarlaAdmin123!'),
            'role': 'ADMIN', 'first_name': 'Local', 'last_name': 'Admin',
            'is_active': True, 'is_staff': False, 'is_superuser': False,
        },
    )


class Migration(migrations.Migration):
    dependencies = [('authentication', '0001_initial')]
    operations = [migrations.RunPython(create_local_admin, migrations.RunPython.noop)]
