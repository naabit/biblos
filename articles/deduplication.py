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


def find_duplicate_doi_groups(articles):
    """
    Recibe un queryset o iterable de Article y devuelve grupos
    con dos o más artículos que comparten el mismo DOI.
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
                "doi": doi,
                "articles": grouped_records,
                "count": len(grouped_records),
            })

    return sorted(
        duplicate_groups,
        key=lambda group: group["doi"],
    )