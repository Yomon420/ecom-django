import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')

# Initialize Django
django.setup()

# Now it's safe to use models
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@gmail.com', 'admin123')
        print("✅ Superuser created: admin/admin123")
except Exception as e:
    print(f"Superuser creation failed: {e}")

# WSGI application
application = get_wsgi_application()
