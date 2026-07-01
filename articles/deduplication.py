import re
import unicodedata
from collections import defaultdict


INVALID_DOI_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
}


def normalize_doi(doi):
    """
    Limpia un DOI para poder comparar registros provenientes
    de distintas fuentes bibliográficas.
    """
    if doi is None:
        return ""

    normalized = str(doi).strip().lower()

    if normalized in INVALID_DOI_VALUES:
        return ""

    normalized = normalized.replace("https://doi.org/", "")
    normalized = normalized.replace("http://doi.org/", "")
    normalized = normalized.replace("doi:", "").strip()

    return normalized


def normalize_title(title):
    """
    Normaliza títulos para comparar variaciones menores:
    - mayúsculas/minúsculas
    - tildes
    - puntuación
    - espacios repetidos
    """
    if title is None:
        return ""

    normalized = str(title).strip().lower()

    if normalized in {"", "nan", "none", "null"}:
        return ""

    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def find_duplicate_doi_groups(articles):
    """
    Devuelve grupos con dos o más artículos que comparten
    el mismo DOI válido.
    """
    grouped_articles = defaultdict(list)

    for article in articles:
        normalized_doi = normalize_doi(article.doi)

        if not normalized_doi:
            continue

        grouped_articles[normalized_doi].append(article)

    duplicate_groups = []

    for doi, grouped_records in grouped_articles.items():
        if len(grouped_records) > 1:
            duplicate_groups.append({
                "type": "doi",
                "label": "Duplicado por DOI",
                "identifier": doi,
                "articles": grouped_records,
                "count": len(grouped_records),
            })

    return sorted(
        duplicate_groups,
        key=lambda group: group["identifier"],
    )


def find_duplicate_title_year_groups(articles):
    """
    Busca posibles duplicados por título normalizado y año.

    Esta regla es menos concluyente que el DOI: solo sirve
    para marcar registros que deben ser revisados manualmente.
    """
    grouped_articles = defaultdict(list)

    for article in articles:
        normalized_title = normalize_title(article.title)

        if not normalized_title or not article.year:
            continue

        key = (normalized_title, article.year)
        grouped_articles[key].append(article)

    duplicate_groups = []

    for (normalized_title, year), grouped_records in grouped_articles.items():
        if len(grouped_records) < 2:
            continue

        unique_dois = {
            normalize_doi(article.doi)
            for article in grouped_records
            if normalize_doi(article.doi)
        }

        # Si todos comparten un mismo DOI válido, ya estarán
        # agrupados arriba como duplicados exactos por DOI.
        if len(unique_dois) == 1 and len(unique_dois) > 0:
            continue

        duplicate_groups.append({
            "type": "title_year",
            "label": "Posible duplicado por título y año",
            "identifier": f"{grouped_records[0].title} ({year})",
            "articles": grouped_records,
            "count": len(grouped_records),
            "year": year,
            "normalized_title": normalized_title,
        })

    return sorted(
        duplicate_groups,
        key=lambda group: group["identifier"].lower(),
    )


def find_duplicate_groups(articles):
    """
    Reúne los grupos detectados por DOI y por título + año.
    """
    doi_groups = find_duplicate_doi_groups(articles)
    title_year_groups = find_duplicate_title_year_groups(articles)

    return doi_groups + title_year_groups