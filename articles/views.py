import pandas as pd

from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages

from .forms import ExcelUploadForm
from .models import Article


def upload_excel(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES["excel_file"]

            try:
                df = pd.read_excel(excel_file)
                print(df.columns.tolist()) #revisar columnas

                for _, row in df.iterrows():

                    year = row.get("PY")

                    if pd.isna(year):
                        year = None
                    else:
                        year = int(year)

                    Article.objects.create(
                        title=str(row.get("TI", "")),
                        authors=str(row.get("AU", "")),
                        year=year,
                        abstract=str(row.get("AB", "")),
                        keywords=str(row.get("KW_Merged", "")),
                        doi=str(row.get("DI", "")),
                        source=str(row.get("SO", "")),
                    )
                        

                messages.success(request, "Archivo importado correctamente.")
                return redirect("article_list")

            except Exception as e:
                messages.error(request, f"Error al importar el archivo: {e}")

    else:
        form = ExcelUploadForm()

    return render(request, "articles/upload_excel.html", {"form": form})

def article_list(request):
    articles = Article.objects.all().order_by("-created_at")

    query = request.GET.get("q")
    status = request.GET.get("status")
    year = request.GET.get("year")

    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(authors__icontains=query) |
            Q(abstract__icontains=query) |
            Q(keywords__icontains=query) |
            Q(doi__icontains=query)
        )

    if status:
        articles = articles.filter(status=status)

    if year:
        articles = articles.filter(year=year)

    years = Article.objects.exclude(year=None).order_by("-year").values_list("year", flat=True).distinct()

    return render(request, "articles/article_list.html", {
        "articles": articles,
        "years": years,
        "query": query,
        "selected_status": status,
        "selected_year": year,
        "status_choices": Article.STATUS_CHOICES,
    })

def update_article_status(request, article_id):
    article = Article.objects.get(id=article_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in dict(Article.STATUS_CHOICES):
            article.status = new_status
            article.save()
            messages.success(request, "Estado actualizado correctamente.")

    return redirect("article_list")