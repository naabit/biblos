from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, JsonResponse

from .forms import ExcelUploadForm
from .models import Article, ExcelUpload


def upload_excel(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                import pandas as pd
            except ModuleNotFoundError:
                messages.error(
                    request,
                    "Falta la dependencia 'pandas'. Instálala (y 'openpyxl') para poder importar Excel.",
                )
                return redirect("article_list")

            excel_file = request.FILES["excel_file"]

            try:
                df = pd.read_excel(excel_file)
                excel_upload = ExcelUpload.objects.create(
                    name=excel_file.name
                )
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
                        excel_upload=excel_upload,
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
    articles = Article.objects.all()

    query = request.GET.get("q")
    status = request.GET.get("status")
    year = request.GET.get("year")
    doi_status = request.GET.get("doi_status")
    sort_by = request.GET.get("sort_by", "")
    sort_direction = request.GET.get("sort_direction", "asc")

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

    sort_direction = sort_direction.lower()
    if sort_direction not in {"asc", "desc"}:
        sort_direction = "asc"

    allowed_sort_fields = {
        "year": "year",
        "title": "title",
        "authors": "authors",
    }

    if sort_by in allowed_sort_fields:
        order_field = allowed_sort_fields[sort_by]
        if sort_direction == "desc":
            order_field = f"-{order_field}"
        articles = articles.order_by(order_field)
    else:
        articles = articles.order_by("-created_at")

    return articles


def article_list(request):
    articles = get_filtered_articles(request)
    sort_by = request.GET.get("sort_by")
    sort_direction = request.GET.get("sort_direction") or "asc"
    excel_uploads = ExcelUpload.objects.all().order_by("-uploaded_at")
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
        "excel_uploads": excel_uploads,
        "years": years,
        "query": query,
        "selected_status": status,
        "selected_year": year,
        "status_choices": Article.STATUS_CHOICES,
        "doi_status": doi_status,
        "selected_sort_by": sort_by,
        "selected_sort_direction": sort_direction,
    })


def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        article.delete()
        messages.success(request, "Artículo eliminado correctamente.")

    return redirect("article_list")


def update_article_status(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in dict(Article.STATUS_CHOICES):
            article.status = new_status
            article.save(update_fields=["status"])
            if is_ajax:
                return JsonResponse({
                    "ok": True,
                    "status": article.status,
                    "status_label": article.get_status_display(),
                })
            messages.success(request, "Estado actualizado correctamente.")
        elif is_ajax:
            return JsonResponse(
                {"ok": False, "error": "Estado inválido."},
                status=400,
            )

    if is_ajax:
        return JsonResponse(
            {"ok": False, "error": "Método no permitido."},
            status=405,
        )

    return redirect("article_list")


def export_clean_excel(request):
    try:
        import pandas as pd
    except ModuleNotFoundError:
        messages.error(
            request,
            "Falta la dependencia 'pandas'. Instálala (y 'openpyxl') para poder exportar a Excel.",
        )
        return redirect("article_list")

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


def delete_excel_upload(request, upload_id):
    excel_upload = get_object_or_404(ExcelUpload, id=upload_id)

    if request.method == "POST":
        name = excel_upload.name
        excel_upload.delete()

        messages.success(
            request,
            f"Se eliminó el Excel '{name}' y todos sus artículos asociados."
        )

    return redirect("article_list")

