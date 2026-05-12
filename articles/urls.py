from django.urls import path
from . import views


urlpatterns = [
    path("", views.article_list, name="article_list"),
    path("upload/", views.upload_excel, name="upload_excel"),
    path("article/<int:article_id>/status/", views.update_article_status, name="update_article_status"),
]