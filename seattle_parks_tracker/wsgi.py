"""
WSGI config for seattle_parks_tracker project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seattle_parks_tracker.settings')
application = get_wsgi_application()
