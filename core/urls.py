from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.contrib import admin
from django.urls import path, include

schema_view = get_schema_view(
    openapi.Info(
        title="Electronic Queue System",
        default_version='v1',
        description="API for RSK",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('chat/', include('apps.chat.urls')),
    # path('user/', include('djoser.urls')),
    # path('login/', include('djoser.urls.jwt')),
    path('', include('apps.users.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('', include('apps.qsystem.urls')),
    path('', include('apps.branches.urls')),
    path('booking/', include('apps.booking.urls')),
    path('admins/', include('apps.admins.urls')),
    path('reports/', include('apps.report_apps.operator_reports.urls')),
    path('reports/', include('apps.report_apps.customer_reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)