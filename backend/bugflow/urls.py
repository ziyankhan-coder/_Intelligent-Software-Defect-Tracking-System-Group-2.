"""
BugFlow URL Configuration
Root URL router connecting all app endpoints.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API health check and root endpoint."""
    return Response({
        'project': 'BugFlow',
        'description': 'Software Issue Tracking & Resolution Platform',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'bugs': '/api/v1/bugs/',
            'projects': '/api/v1/projects/',
            'ai': '/api/v1/ai/',
            'admin': '/admin/',
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API root health check
    path('api/', api_root, name='api_root'),
    path('api/v1/', api_root, name='api_v1_root'),

    # Authentication & Users (Ziyan - Week 1)
    path('api/v1/auth/', include('apps.users.urls')),

    # Issue Tracking (Ziyan - Week 1)
    path('api/v1/bugs/', include('apps.issues.urls')),

    # Projects & Collaboration (Nandhini - Week 1)
    path('api/v1/projects/', include('apps.collab.urls')),

    # AI Triage (Sreevarshini - AI & Smart Logic)
    path('api/v1/ai/', include('apps.ai_triage.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
