from django.urls import path
from . import views

urlpatterns = [
    path("list", views.document_list, name="document_list"),
    path("", views.upload_document, name="upload_document"),
]
