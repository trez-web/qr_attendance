from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from attendance import views
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.user_login, name='user_login'),
    path('attendance/', include('attendance.urls')),
    # Serve static files (admin CSS/JS) via gunicorn
    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    # Serve media files
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
