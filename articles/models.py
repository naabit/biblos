from django.db import models

class ExcelUpload(models.Model):
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    excel_upload = models.ForeignKey(
    ExcelUpload,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="articles"
    )
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("included", "Incluido"),
        ("excluded", "Excluido"),
        ("review", "Revisar después"),
    ]

    title = models.TextField(verbose_name="Título")
    authors = models.TextField(blank=True, verbose_name="Autores")
    year = models.IntegerField(null=True, blank=True, verbose_name="Año")
    abstract = models.TextField(blank=True, verbose_name="Resumen")
    keywords = models.TextField(blank=True, verbose_name="Palabras clave")
    doi = models.CharField(max_length=255, blank=True, verbose_name="DOI")
    source = models.CharField(max_length=100, blank=True, verbose_name="Fuente")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Estado"
    )

    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title[:80]