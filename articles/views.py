import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse

from .forms import ExcelUploadForm
from .models import Article


def upload_excel(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES["excel_file"]

            try:
                df = pd.read_excel(excel_file)
                print(df.columns.tolist())

                for _, row in df.iterrows():
                    year = row.get("PY")

                    if pd.isna(year):
                        year = None
                    else:
                        year = int(year)

                    doi = row.get("DI")

                    if pd.isna(doi):
                        doi = ""
                    else:
                        doi = str(doi).strip()

                    Article.objects.create(
                        title=str(row.get("TI", "")),
                        authors=str(row.get("AU", "")),
                        year=year,
                        abstract=str(row.get("AB", "")),
                        keywords=str(row.get("KW_Merged", "")),
                        doi=doi,
                        source=str(row.get("SO", "")),
                    )

                messages.success(request, "Archivo importado correctamente.")
                return redirect("article_list")

            except Exception as e:
                messages.error(request, f"Error al importar el archivo: {e}")

    else:
        form = ExcelUploadForm()

    return render(request, "articles/upload_excel.html", {"form": form})


def get_filtered_articles(request):
    articles = Article.objects.all().order_by("-created_at")

    query = request.GET.get("q")
    status = request.GET.get("status")
    year = request.GET.get("year")
    doi_status = request.GET.get("doi_status")

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

    if doi_status == "with":
        articles = articles.exclude(
            Q(doi="") |
            Q(doi__isnull=True) |
            Q(doi__iexact="nan")
        )

    if doi_status == "without":
        articles = articles.filter(
            Q(doi="") |
            Q(doi__isnull=True) |
            Q(doi__iexact="nan")
        )

    return articles


def article_list(request):
    articles = get_filtered_articles(request)

    query = request.GET.get("q")
    status = request.GET.get("status")
    year = request.GET.get("year")
    doi_status = request.GET.get("doi_status")

    years = (
        Article.objects
        .exclude(year=None)
        .order_by("-year")
        .values_list("year", flat=True)
        .distinct()
    )

    return render(request, "articles/article_list.html", {
        "articles": articles,
        "years": years,
        "query": query,
        "selected_status": status,
        "selected_year": year,
        "status_choices": Article.STATUS_CHOICES,
        "doi_status": doi_status,
    })


def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        article.delete()
        messages.success(request, "Artículo eliminado correctamente.")

    return redirect("article_list")


def update_article_status(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in dict(Article.STATUS_CHOICES):
            article.status = new_status
            article.save()
            messages.success(request, "Estado actualizado correctamente.")

    return redirect("article_list")


def export_clean_excel(request):
    articles = get_filtered_articles(request).order_by("year", "title")

    data = []

    for article in articles:
        data.append({
            "Título": article.title,
            "Autores": article.authors,
            "Año": article.year,
            "Fuente": article.source,
            "DOI": article.doi,
            "Resumen": article.abstract,
            "Palabras clave": article.keywords,
            "Estado": article.get_status_display(),
            "Notas": article.notes,
        })

    df = pd.DataFrame(data)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="biblos_articulos_filtrados.xlsx"'

    df.to_excel(response, index=False)

    return response

def delete_all_articles(request):

    if request.method == "POST":
        total = Article.objects.count()

        Article.objects.all().delete()

        messages.success(
            request,
            f"Se eliminaron {total} artículos correctamente."
        )

    return redirect("article_list")