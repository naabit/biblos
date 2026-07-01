from django.contrib import admin
from .models import Article

from django.contrib import admin

from .models import Article, ExcelUpload


@admin.register(ExcelUpload)
class ExcelUploadAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "source_database",
        "session_key",
        "uploaded_at",
    )
    list_filter = ("source_database", "uploaded_at")
    search_fields = ("name", "session_key")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "year",
        "doi",
        "source",
        "external_id",
        "status",
    )
    list_filter = ("status", "year")
    search_fields = (
        "title",
        "authors",
        "doi",
        "external_id",
        "source",
    )