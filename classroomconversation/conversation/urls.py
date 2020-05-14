from django.urls import path, include

from . import views

urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("list", views.document_list, name="document_list"),
    path("", views.upload_document, name="upload_document"),
]
