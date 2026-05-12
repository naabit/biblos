from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "source", "status")
    list_filter = ("status", "year", "source")
    search_fields = ("title", "authors", "abstract", "keywords", "doi")