import re
import pandas as pd


def clean_value(value):
    """
    Convierte valores de Pandas a texto limpio y evita guardar
    'nan', 'None' o valores vacíos como texto.
    """
    if value is None:
        return ""

    if isinstance(value, float) and pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() in {"nan", "none", "nat"}:
        return ""

    return value


def parse_year(value):
    """
    Intenta extraer un año válido desde valores como:
    2024, '2024', '2024-01-01' o texto que incluya un año.
    """
    value = clean_value(value)

    if not value:
        return None

    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2}|21\d{2})\b", value)

    if not match:
        return None

    return int(match.group())


def normalize_header(header):
    """
    Normaliza encabezados para comparar columnas sin depender
    de mayúsculas, espacios o pequeñas variaciones.
    """
    return " ".join(str(header).strip().lower().split())


def build_column_lookup(dataframe):
    """
    Crea un diccionario como:
    {'article title': 'Article Title', 'doi': 'DOI'}
    """
    return {
        normalize_header(column): column
        for column in dataframe.columns
    }


def find_column(column_lookup, possible_names):
    """
    Busca la primera columna disponible dentro de una lista
    de posibles nombres equivalentes.
    """
    for name in possible_names:
        normalized_name = normalize_header(name)

        if normalized_name in column_lookup:
            return column_lookup[normalized_name]

    return None


def get_row_value(row, column_lookup, possible_names):
    """
    Obtiene una celda usando distintos nombres posibles de columna.
    """
    column = find_column(column_lookup, possible_names)

    if not column:
        return ""

    return clean_value(row.get(column))


def get_combined_values(row, column_lookup, possible_names):
    """
    Une campos equivalentes, útil para palabras clave provenientes
    de más de una columna.
    """
    values = []

    for name in possible_names:
        column = find_column(column_lookup, [name])

        if not column:
            continue

        value = clean_value(row.get(column))

        if value and value not in values:
            values.append(value)

    return "; ".join(values)


def detect_source_database(dataframe):
    """
    Detecta de forma simple el origen probable del archivo.
    No bloquea la importación si no logra identificarlo.
    """
    headers = {
        normalize_header(column)
        for column in dataframe.columns
    }

    scopus_signals = {
        "eid",
        "source title",
        "author full names",
        "index keywords",
        "publication stage",
        "cited by",
    }

    wos_signals = {
        "ut",
        "unique wos id",
        "article title",
        "publication year",
        "author keywords",
        "keywords plus",
        "times cited, wos core",
    }

    legacy_wos_signals = {
        "ti",
        "au",
        "py",
        "di",
        "ab",
        "so",
    }

    if headers.intersection(scopus_signals):
        return "scopus"

    if headers.intersection(wos_signals):
        return "wos"

    if len(headers.intersection(legacy_wos_signals)) >= 3:
        return "wos"

    return "unknown"


def normalize_bibliographic_records(dataframe):
    """
    Convierte registros de Scopus, Web of Science o formatos
    compatibles a la estructura interna de Article.
    """
    column_lookup = build_column_lookup(dataframe)
    source_database = detect_source_database(dataframe)

    records = []
    skipped_rows = 0

    for _, row in dataframe.iterrows():
        title = get_row_value(
            row,
            column_lookup,
            [
                "TI",
                "Title",
                "Article Title",
                "Document Title",
            ],
        )

        # Un artículo sin título no es útil ni trazable.
        if not title:
            skipped_rows += 1
            continue

        authors = get_row_value(
            row,
            column_lookup,
            [
                "AU",
                "Authors",
                "Author Full Names",
                "Author(s)",
            ],
        )

        year = parse_year(
            get_row_value(
                row,
                column_lookup,
                [
                    "PY",
                    "Year",
                    "Publication Year",
                    "Published Year",
                ],
            )
        )

        abstract = get_row_value(
            row,
            column_lookup,
            [
                "AB",
                "Abstract",
                "Description",
            ],
        )

        keywords = get_combined_values(
            row,
            column_lookup,
            [
                "KW_Merged",
                "KW",
                "DE",
                "ID",
                "Author Keywords",
                "Index Keywords",
                "Keywords Plus",
                "Keywords",
            ],
        )

        doi = get_row_value(
            row,
            column_lookup,
            [
                "DI",
                "DOI",
                "Digital Object Identifier",
            ],
        )

        source = get_row_value(
            row,
            column_lookup,
            [
                "SO",
                "Source Title",
                "Source title",
                "Journal",
                "Publication Name",
            ],
        )

        external_id = get_row_value(
            row,
            column_lookup,
            [
                "EID",
                "UT",
                "Unique WOS ID",
            ],
        )

        records.append({
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": abstract,
            "keywords": keywords,
            "doi": doi,
            "source": source,
            "external_id": external_id,
        })

    return {
        "source_database": source_database,
        "records": records,
        "skipped_rows": skipped_rows,
    }


def read_bibliographic_file(uploaded_file):
    """
    Lee archivos Excel o CSV según su extensión.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)