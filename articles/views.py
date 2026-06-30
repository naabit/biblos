from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, JsonResponse

from .forms import ExcelUploadForm
from .models import Article, ExcelUpload
from .utils import get_or_create_session_key

from django.db import transaction

from .importers import (
    normalize_bibliographic_records,
    read_bibliographic_file,
)

def upload_excel(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                import pandas as pd  # noqa: F401
            except ModuleNotFoundError:
                messages.error(
                    request,
                    "Falta la dependencia 'pandas'. Instálala junto con "
                    "'openpyxl' para poder importar archivos bibliográficos.",
                )
                return redirect("article_list")

            excel_file = request.FILES["excel_file"]
            session_key = get_or_create_session_key(request)

            try:
                dataframe = read_bibliographic_file(excel_file)

                import_result = normalize_bibliographic_records(dataframe)

                records = import_result["records"]
                source_database = import_result["source_database"]
                skipped_rows = import_result["skipped_rows"]

                if not records:
                    messages.error(
                        request,
                        "No se encontraron artículos válidos. "
                        "Revisa que el archivo contenga al menos una columna de título.",
                    )
                    return redirect("article_list")

                with transaction.atomic():
                    excel_upload = ExcelUpload.objects.create(
                        session_key=session_key,
                        name=excel_file.name,
                        source_database=source_database,
                    )

                    articles = [
                        Article(
                            excel_upload=excel_upload,
                            title=record["title"],
                            authors=record["authors"],
                            year=record["year"],
                            abstract=record["abstract"],
                            keywords=record["keywords"],
                            doi=record["doi"],
                            source=record["source"],
                            external_id=record["external_id"],
                        )
                        for record in records
                    ]

                    Article.objects.bulk_create(
                        articles,
                        batch_size=500,
                    )

                source_label = excel_upload.get_source_database_display()

                message = (
                    f"Archivo importado correctamente: "
                    f"{len(records)} artículos desde {source_label}."
                )

                if skipped_rows:
                    message += (
                        f" Se omitieron {skipped_rows} filas sin título."
                    )

                messages.success(request, message)

                return redirect("article_list")

            except Exception as error:
                messages.error(
                    request,
                    f"Error al importar el archivo: {error}",
                )

    else:
        form = ExcelUploadForm()

    return render(request, "articles/upload_excel.html", {"form": form})

def get_filtered_articles(request):
    session_key = get_or_create_session_key(request)

    articles = Article.objects.filter(
        excel_upload__session_key=session_key
    )

    query = request.GET.get("q")
    status = request.GET.get("status")
    year = request.GET.get("year")
    doi_status = request.GET.get("doi_status")
    sort_by = request.GET.get("sort_by", "")
    sort_direction = request.GET.get("sort_direction", "asc")

    if query:
        articles = articles.filter(
            Q(title__icontains=query)
            | Q(authors__icontains=query)
            | Q(abstract__icontains=query)
            | Q(keywords__icontains=query)
            | Q(doi__icontains=query)
        )

    if status:
        articles = articles.filter(status=status)

    if year:
        articles = articles.filter(year=year)

    if doi_status == "with":
        articles = articles.exclude(
            Q(doi="")
            | Q(doi__isnull=True)
            | Q(doi__iexact="nan")
        )

    if doi_status == "without":
        articles = articles.filter(
            Q(doi="")
            | Q(doi__isnull=True)
            | Q(doi__iexact="nan")
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
    session_key = get_or_create_session_key(request)

    articles = get_filtered_articles(request)

    sort_by = request.GET.get("sort_by")
    sort_direction = request.GET.get("sort_direction") or "asc"

    excel_uploads = ExcelUpload.objects.filter(
        session_key=session_key
    ).order_by("-uploaded_at")

    query = request.GET.get("q")
    status = request.GET.get("status")
    year = request.GET.get("year")
    doi_status = request.GET.get("doi_status")

    years = (
        Article.objects
        .filter(excel_upload__session_key=session_key)
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
    session_key = get_or_create_session_key(request)

    article = get_object_or_404(
        Article,
        id=article_id,
        excel_upload__session_key=session_key,
    )

    if request.method == "POST":
        article.delete()
        messages.success(request, "Artículo eliminado correctamente.")

    return redirect("article_list")


def update_article_status(request, article_id):
    session_key = get_or_create_session_key(request)

    article = get_object_or_404(
        Article,
        id=article_id,
        excel_upload__session_key=session_key,
    )

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
                {"ok": False, "error": "Estado invalido."},
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
            "Falta la dependencia 'pandas'. Instála junto con 'openpyxl' para poder exportar a Excel.",
        )
        return redirect("article_list")

    articles = get_filtered_articles(request).order_by("year", "title")

    data = []

    for article in articles:
        data.append({
            "Título": article.title,
            "Autores": article.authors,
            "Año": article.year,
            "Fuente de publicación": article.source,
            "Base de datos de origen": article.excel_upload.get_source_database_display(),
            "Identificador externo": article.external_id,
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

    response["Content-Disposition"] = (
        'attachment; filename="biblos_articulos_filtrados.xlsx"'
    )

    df.to_excel(response, index=False)

    return response


def delete_all_articles(request):
    session_key = get_or_create_session_key(request)

    if request.method == "POST":
        articles = Article.objects.filter(
            excel_upload__session_key=session_key
        )

        total = articles.count()
        articles.delete()

        ExcelUpload.objects.filter(
            session_key=session_key
        ).delete()

        messages.success(
            request,
            f"Se eliminaron {total} artículos correctamente.",
        )

    return redirect("article_list")


def delete_excel_upload(request, upload_id):
    session_key = get_or_create_session_key(request)

    excel_upload = get_object_or_404(
        ExcelUpload,
        id=upload_id,
        session_key=session_key,
    )

    if request.method == "POST":
        name = excel_upload.name
        excel_upload.delete()

        messages.success(
            request,
            f"Se eliminó el Excel '{name}' y todos sus artículos asociados.",
        )

    return redirect("article_list")
