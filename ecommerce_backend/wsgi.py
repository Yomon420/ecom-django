import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    # Use the field that identifies your user, likely 'email'
    if not User.objects.filter(email='admin@gmail.com').exists():
        User.objects.create_superuser(
            email='admin@gmail.com',
            password='admin123'
        )
        print("✅ Superuser created: admin@gmail.com / admin123")
except Exception as e:
    print(f"Superuser creation failed: {e}")

application = get_wsgi_application()
