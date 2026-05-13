from django.urls import path
from . import views


urlpatterns = [
    path("", views.article_list, name="article_list"),
    path("upload/", views.upload_excel, name="upload_excel"),
    path("article/<int:article_id>/status/", views.update_article_status, name="update_article_status"),
    path("export/", views.export_clean_excel, name="export_clean_excel"),
    path(
    "articles/<int:article_id>/delete/",
    views.delete_article,
    name="delete_article"),
    path(
        "articles/delete-all/",
        views.delete_all_articles,
        name="delete_all_articles"
    ),
    path(
    "excel-upload/<int:upload_id>/delete/",
    views.delete_excel_upload,
    name="delete_excel_upload"
    ),
]