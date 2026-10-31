from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),

    # Documentation OpenAPI / Swagger pour le collègue Frontend (TanStack)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Endpoints API REST v1
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/properties/', include('apps.properties.urls')),
    path('api/v1/simulators/', include('apps.simulators.urls')),
    path('api/v1/crm/', include('apps.crm.urls')),
]

# Servir les images uploadées en développement local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
