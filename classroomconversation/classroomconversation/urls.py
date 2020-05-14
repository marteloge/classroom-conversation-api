from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from conversation import views as conversation_views

router = routers.DefaultRouter()
router.register(r"documents", conversation_views.ConversationViewSet)


urlpatterns = [
    path("upload/", include("conversation.urls")),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
