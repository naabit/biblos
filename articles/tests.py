from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test.utils import modify_settings
from django.urls import reverse

from .deduplication import (
    find_duplicate_doi_groups,
    find_duplicate_groups,
    normalize_doi,
    normalize_title,
)
from .models import Article, ExcelUpload


class FakeImportDataFrame:
    """
    Replica la parte mínima de pandas.DataFrame que usa
    la importación normalizada.
    """

    def __init__(self, rows):
        self.rows = rows
        self.columns = list(rows[0].keys()) if rows else []

    def iterrows(self):
        for index, row in enumerate(self.rows):
            yield index, row


class FakeExportDataFrame:
    """
    Conserva la última instancia para inspeccionar qué intentó
    exportar la vista.
    """

    last_instance = None

    def __init__(self, rows):
        self.rows = rows
        self.export_calls = []
        FakeExportDataFrame.last_instance = self

    def to_excel(self, response, index=False):
        self.export_calls.append({
            "response": response,
            "index": index,
        })


def make_fake_pandas_for_export():
    """
    La vista importa pandas dentro de la función al exportar.
    Este stub evita generar un Excel real durante el test.
    """
    return type(
        "FakePandas",
        (),
        {"DataFrame": FakeExportDataFrame},
    )


@modify_settings(MIDDLEWARE={"remove": ["whitenoise.middleware.WhiteNoiseMiddleware"]})
class ArticlesViewTests(TestCase):
    def setUp(self):
        """
        Dos clientes distintos permiten validar el aislamiento
        de artículos y cargas según session_key.
        """
        self.client = Client()
        session = self.client.session
        session.save()
        self.session_key = session.session_key

        self.other_client = Client()
        other_session = self.other_client.session
        other_session.save()
        self.other_session_key = other_session.session_key

    def create_upload(
        self,
        session_key,
        name="dataset.xlsx",
        source_database="unknown",
    ):
        return ExcelUpload.objects.create(
            session_key=session_key,
            name=name,
            source_database=source_database,
        )

    def create_article(self, session_key=None, upload=None, **overrides):
        """
        Centraliza fixtures con defaults realistas para que
        cada test modifique solo lo que necesita.
        """
        if upload is None:
            upload = self.create_upload(session_key or self.session_key)

        data = {
            "excel_upload": upload,
            "title": "Default title",
            "authors": "Default author",
            "year": 2024,
            "abstract": "Default abstract",
            "keywords": "Default keywords",
            "doi": "10.1000/default",
            "source": "Default source",
            "external_id": "",
            "status": "pending",
        }
        data.update(overrides)

        return Article.objects.create(**data)

    def test_upload_excel_get_renders_form(self):
        response = self.client.get(reverse("upload_excel"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "articles/upload_excel.html")
        self.assertIn("form", response.context)

    def test_upload_excel_post_creates_articles_and_normalizes_fields(self):
        fake_dataframe = FakeImportDataFrame([
            {
                "TI": "First article",
                "AU": "Alice",
                "PY": 2024.0,
                "AB": "Abstract 1",
                "KW_Merged": "testing",
                "DI": " 10.1000/first ",
                "SO": "Journal 1",
                "UT": "WOS:000001",
            },
            {
                "TI": "Second article",
                "AU": "Bob",
                "PY": float("nan"),
                "AB": "Abstract 2",
                "KW_Merged": "coverage",
                "DI": float("nan"),
                "SO": "Journal 2",
                "UT": "WOS:000002",
            },
        ])

        excel_file = SimpleUploadedFile(
            "articles.xlsx",
            b"fake excel content",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        with patch(
            "articles.views.read_bibliographic_file",
            return_value=fake_dataframe,
        ):
            response = self.client.post(
                reverse("upload_excel"),
                {"excel_file": excel_file},
            )

        self.assertRedirects(response, reverse("article_list"))
        self.assertEqual(ExcelUpload.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 2)

        first_article = Article.objects.get(title="First article")
        second_article = Article.objects.get(title="Second article")
        upload = ExcelUpload.objects.get()

        self.assertEqual(upload.session_key, self.session_key)
        self.assertEqual(upload.name, "articles.xlsx")
        self.assertEqual(upload.source_database, "wos")

        self.assertEqual(first_article.year, 2024)
        self.assertEqual(first_article.doi, "10.1000/first")
        self.assertEqual(first_article.external_id, "WOS:000001")

        self.assertIsNone(second_article.year)
        self.assertEqual(second_article.doi, "")
        self.assertEqual(second_article.external_id, "WOS:000002")

    def test_article_list_only_shows_articles_from_current_session(self):
        own_upload = self.create_upload(self.session_key, "own.xlsx")
        other_upload = self.create_upload(
            self.other_session_key,
            "other.xlsx",
        )

        own_article = self.create_article(
            upload=own_upload,
            title="Visible article",
        )
        self.create_article(upload=other_upload, title="Hidden article")

        response = self.client.get(reverse("article_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["articles"]), [own_article])
        self.assertEqual(list(response.context["excel_uploads"]), [own_upload])
        self.assertContains(response, "Visible article")
        self.assertNotContains(response, "Hidden article")

    def test_article_list_filters_by_query_status_year_doi_and_sort(self):
        upload = self.create_upload(self.session_key)

        self.create_article(
            upload=upload,
            title="Zeta paper",
            authors="Alice",
            year=2024,
            abstract="Neural networks",
            keywords="ml",
            doi="10.1000/zeta",
            status="included",
        )
        self.create_article(
            upload=upload,
            title="Alpha paper",
            authors="Bob",
            year=2024,
            abstract="Neural imaging",
            keywords="brain",
            doi="10.1000/alpha",
            status="included",
        )
        self.create_article(
            upload=upload,
            title="No DOI paper",
            authors="Carol",
            year=2024,
            abstract="Neural imaging",
            keywords="brain",
            doi="",
            status="included",
        )
        self.create_article(
            upload=upload,
            title="Excluded paper",
            authors="Dave",
            year=2023,
            abstract="Neural imaging",
            keywords="brain",
            doi="10.1000/excluded",
            status="excluded",
        )

        response = self.client.get(
            reverse("article_list"),
            {
                "q": "Neural",
                "status": "included",
                "year": "2024",
                "doi_status": "with",
                "sort_by": "title",
                "sort_direction": "desc",
            },
        )

        articles = list(response.context["articles"])

        self.assertEqual(
            [article.title for article in articles],
            ["Zeta paper", "Alpha paper"],
        )
        self.assertEqual(response.context["selected_status"], "included")
        self.assertEqual(response.context["selected_year"], "2024")
        self.assertEqual(response.context["doi_status"], "with")
        self.assertEqual(response.context["selected_sort_by"], "title")
        self.assertEqual(response.context["selected_sort_direction"], "desc")

    def test_update_article_status_ajax_updates_article(self):
        article = self.create_article(status="pending")

        response = self.client.post(
            reverse("update_article_status", args=[article.id]),
            {"status": "included"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        article.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "status": "included",
                "status_label": "Incluido",
            },
        )
        self.assertEqual(article.status, "included")

    def test_update_article_status_ajax_rejects_invalid_status(self):
        article = self.create_article(status="pending")

        response = self.client.post(
            reverse("update_article_status", args=[article.id]),
            {"status": "invalid"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        article.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(article.status, "pending")

    def test_update_article_status_redirects_to_next_url(self):
        article = self.create_article(status="pending")

        response = self.client.post(
            reverse("update_article_status", args=[article.id]),
            {
                "status": "included",
                "next": reverse("duplicate_list"),
            },
        )

        article.refresh_from_db()

        self.assertRedirects(response, reverse("duplicate_list"))
        self.assertEqual(article.status, "included")

    def test_delete_article_only_allows_access_to_current_session(self):
        own_article = self.create_article(title="Own article")
        other_upload = self.create_upload(self.other_session_key)
        other_article = self.create_article(
            upload=other_upload,
            title="Other article",
        )

        response = self.client.post(
            reverse("delete_article", args=[own_article.id])
        )

        self.assertRedirects(response, reverse("article_list"))
        self.assertFalse(
            Article.objects.filter(id=own_article.id).exists()
        )

        response = self.client.post(
            reverse("delete_article", args=[other_article.id])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Article.objects.filter(id=other_article.id).exists()
        )

    def test_delete_article_redirects_to_next_url(self):
        article = self.create_article(title="Own article")

        response = self.client.post(
            reverse("delete_article", args=[article.id]),
            {"next": reverse("duplicate_list")},
        )

        self.assertRedirects(response, reverse("duplicate_list"))
        self.assertFalse(Article.objects.filter(id=article.id).exists())

    def test_delete_all_articles_only_clears_current_session(self):
        own_upload = self.create_upload(self.session_key, "own.xlsx")
        other_upload = self.create_upload(
            self.other_session_key,
            "other.xlsx",
        )

        self.create_article(upload=own_upload, title="Own 1")
        self.create_article(upload=own_upload, title="Own 2")
        self.create_article(upload=other_upload, title="Other 1")

        response = self.client.post(reverse("delete_all_articles"))

        self.assertRedirects(response, reverse("article_list"))
        self.assertEqual(
            Article.objects.filter(
                excel_upload__session_key=self.session_key
            ).count(),
            0,
        )
        self.assertEqual(
            ExcelUpload.objects.filter(
                session_key=self.session_key
            ).count(),
            0,
        )
        self.assertEqual(
            Article.objects.filter(
                excel_upload__session_key=self.other_session_key
            ).count(),
            1,
        )
        self.assertEqual(
            ExcelUpload.objects.filter(
                session_key=self.other_session_key
            ).count(),
            1,
        )

    def test_duplicate_list_only_shows_duplicate_groups_from_current_session(self):
        own_upload = self.create_upload(
            self.session_key,
            "own.xlsx",
            source_database="wos",
        )
        other_upload = self.create_upload(
            self.other_session_key,
            "other.xlsx",
            source_database="scopus",
        )

        self.create_article(
            upload=own_upload,
            title="Own duplicate one",
            doi="10.1000/own.001",
        )
        self.create_article(
            upload=own_upload,
            title="Own duplicate two",
            doi="doi:10.1000/OWN.001",
        )

        self.create_article(
            upload=other_upload,
            title="Other duplicate one",
            doi="10.1000/other.001",
        )
        self.create_article(
            upload=other_upload,
            title="Other duplicate two",
            doi="10.1000/other.001",
        )

        response = self.client.get(reverse("duplicate_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "articles/duplicate_list.html")
        self.assertEqual(len(response.context["duplicate_groups"]), 1)
        self.assertContains(response, "Own duplicate one")
        self.assertNotContains(response, "Other duplicate one")

    def test_export_clean_excel_exports_filtered_articles(self):
        upload = self.create_upload(
            self.session_key,
            source_database="wos",
        )
        self.create_article(
            upload=upload,
            title="Included paper",
            authors="Alice",
            year=2024,
            abstract="Abstract",
            keywords="kw",
            doi="10.1000/included",
            source="Journal",
            external_id="WOS:000123",
            status="included",
        )
        self.create_article(
            upload=upload,
            title="Pending paper",
            year=2023,
            doi="",
            status="pending",
        )
        other_upload = self.create_upload(self.other_session_key)
        self.create_article(
            upload=other_upload,
            title="Other session paper",
            year=2024,
            doi="10.1000/other",
            status="included",
        )

        FakeExportDataFrame.last_instance = None
        fake_pandas = make_fake_pandas_for_export()

        with patch.dict("sys.modules", {"pandas": fake_pandas}):
            response = self.client.get(
                reverse("export_clean_excel"),
                {
                    "status": "included",
                    "doi_status": "with",
                },
            )

        exported_frame = FakeExportDataFrame.last_instance

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        self.assertIn(
            "biblos_articulos_filtrados.xlsx",
            response["Content-Disposition"],
        )
        self.assertIsNotNone(exported_frame)
        self.assertFalse(exported_frame.export_calls[0]["index"])

        self.assertEqual(
            exported_frame.rows,
            [{
                "Título": "Included paper",
                "Autores": "Alice",
                "Año": 2024,
                "Fuente de publicación": "Journal",
                "Base de datos de origen": "Web of Science",
                "Identificador externo": "WOS:000123",
                "DOI": "10.1000/included",
                "Resumen": "Abstract",
                "Palabras clave": "kw",
                "Estado": "Incluido",
                "Notas": "",
            }],
        )


class DeduplicationTests(TestCase):
    def setUp(self):
        self.session_key = "deduplication-test-session"

    def create_upload(self, source_database="unknown"):
        return ExcelUpload.objects.create(
            session_key=self.session_key,
            name="deduplication.xlsx",
            source_database=source_database,
        )

    def create_article(self, upload, **overrides):
        data = {
            "excel_upload": upload,
            "title": "Default title",
            "authors": "Default author",
            "year": 2024,
            "abstract": "",
            "keywords": "",
            "doi": "",
            "source": "",
            "external_id": "",
            "status": "pending",
        }
        data.update(overrides)

        return Article.objects.create(**data)

    def test_normalize_doi_removes_common_prefixes(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1000/TEST.001"),
            "10.1000/test.001",
        )
        self.assertEqual(
            normalize_doi("doi: 10.1000/test.001"),
            "10.1000/test.001",
        )
        self.assertEqual(normalize_doi("nan"), "")
        self.assertEqual(normalize_doi(""), "")

    def test_normalize_title_ignores_accents_case_and_punctuation(self):
        first_title = "Inteligencia Artificial: una revisión."
        second_title = "inteligencia artificial una revision"

        self.assertEqual(
            normalize_title(first_title),
            normalize_title(second_title),
        )

    def test_find_duplicate_doi_groups_groups_same_doi(self):
        upload = self.create_upload()

        first_article = self.create_article(
            upload,
            title="Artículo desde Scopus",
            doi="https://doi.org/10.1000/duplicate.001",
        )
        second_article = self.create_article(
            upload,
            title="Artículo desde WoS",
            doi="doi:10.1000/DUPLICATE.001",
        )

        groups = find_duplicate_doi_groups(
            Article.objects.filter(
                excel_upload__session_key=self.session_key
            )
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["type"], "doi")
        self.assertEqual(
            groups[0]["identifier"],
            "10.1000/duplicate.001",
        )
        self.assertEqual(groups[0]["count"], 2)
        self.assertEqual(
            {article.id for article in groups[0]["articles"]},
            {first_article.id, second_article.id},
        )

    def test_find_duplicate_groups_detects_title_and_year_without_doi(self):
        upload = self.create_upload()

        first_article = self.create_article(
            upload,
            title="Tecnología y desigualdad: una revisión",
            year=2024,
            doi="",
        )
        second_article = self.create_article(
            upload,
            title="tecnologia y desigualdad una revision.",
            year=2024,
            doi="",
        )

        groups = find_duplicate_groups(
            Article.objects.filter(
                excel_upload__session_key=self.session_key
            )
        )

        title_year_groups = [
            group
            for group in groups
            if group["type"] == "title_year"
        ]

        self.assertEqual(len(title_year_groups), 1)
        self.assertEqual(title_year_groups[0]["count"], 2)
        self.assertEqual(
            {article.id for article in title_year_groups[0]["articles"]},
            {first_article.id, second_article.id},
        )

    def test_find_duplicate_groups_does_not_match_same_title_with_different_years(self):
        upload = self.create_upload()

        self.create_article(
            upload,
            title="Tecnología y desigualdad",
            year=2023,
            doi="",
        )
        self.create_article(
            upload,
            title="Tecnología y desigualdad",
            year=2024,
            doi="",
        )

        groups = find_duplicate_groups(
            Article.objects.filter(
                excel_upload__session_key=self.session_key
            )
        )

        title_year_groups = [
            group
            for group in groups
            if group["type"] == "title_year"
        ]

        self.assertEqual(title_year_groups, [])

    def test_find_duplicate_groups_avoids_repeating_exact_doi_as_title_year(self):
        upload = self.create_upload()

        self.create_article(
            upload,
            title="Artículo repetido",
            year=2025,
            doi="10.1000/repeated.001",
        )
        self.create_article(
            upload,
            title="Artículo repetido",
            year=2025,
            doi="10.1000/repeated.001",
        )

        groups = find_duplicate_groups(
            Article.objects.filter(
                excel_upload__session_key=self.session_key
            )
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["type"], "doi")
