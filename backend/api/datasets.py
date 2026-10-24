"""Dataset browser routes plus the example verses and transliteration schemes."""

import csv
import json
import logging

from flask import Blueprint, current_app, jsonify, request

from backend.api.helpers import SOURCE_DIR
from backend.config import settings

logger = logging.getLogger(__name__)

bp = Blueprint('datasets', __name__)


def load_dataset_catalog():
    """Load the dataset catalog from JSON file."""
    catalog_path = SOURCE_DIR / 'dataset_sources.json'
    if catalog_path.exists():
        with open(catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"datasets": {}, "sourceDescriptions": {}}


def read_csv_data(filename, limit=None, offset=0, chandas_filter=None, source_filter=None):
    """
    Read CSV data with optional filtering and pagination.

    Args:
        filename: CSV filename in source directory
        limit: Max rows to return (None = all)
        offset: Rows to skip for pagination
        chandas_filter: Filter by chandas name (substring match)
        source_filter: Filter by source (not applicable for CSVs without source column)

    Returns:
        tuple: (rows, total_count, columns)
    """
    filepath = SOURCE_DIR / filename
    if not filepath.exists():
        return [], 0, []

    rows = []
    columns = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []

        all_rows = list(reader)

        # Apply chandas filter if specified
        if chandas_filter:
            catalog = load_dataset_catalog()
            dataset_info = None
            for _ds_id, ds_data in catalog.get('datasets', {}).items():
                if ds_data.get('filename') == filename:
                    dataset_info = ds_data
                    break

            if dataset_info and dataset_info.get('chandasColumn'):
                chandas_col = dataset_info['chandasColumn']
                chandas_filter_lower = chandas_filter.lower()
                all_rows = [
                    row for row in all_rows if chandas_col in row and chandas_filter_lower in row[chandas_col].lower()
                ]

        total_count = len(all_rows)

        # Apply pagination
        if offset:
            all_rows = all_rows[offset:]
        if limit:
            all_rows = all_rows[:limit]

        rows = all_rows

    return rows, total_count, columns


def get_unique_chandas(filename, chandas_column):
    """Get unique chandas values from a dataset."""
    filepath = SOURCE_DIR / filename
    if not filepath.exists():
        return []

    chandas_set = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if chandas_column in row and row[chandas_column].strip():
                # Handle multiple chandas in one cell (comma-separated)
                values = row[chandas_column].split(',')
                for v in values:
                    v = v.strip()
                    if v:
                        chandas_set.add(v)

    return sorted(list(chandas_set))


@bp.route(f'{settings.API_PREFIX}/datasets', methods=['GET'])
def list_datasets():
    """
    List all available datasets with metadata.

    Returns:
        JSON with list of datasets and their metadata
    """
    try:
        catalog = load_dataset_catalog()
        datasets = []

        for ds_id, ds_data in catalog.get('datasets', {}).items():
            # Handle merged datasets (like iitk_meters)
            if 'files' in ds_data:
                # Merged dataset - count rows from all files
                actual_row_count = 0
                unique_chandas_set = set()
                for file_info in ds_data['files']:
                    filepath = SOURCE_DIR / file_info.get('filename', '')
                    if filepath.exists():
                        with open(filepath, 'r', encoding='utf-8') as f:
                            actual_row_count += sum(1 for _ in f) - 1
                        # Get unique chandas from each file
                        chandas_col = file_info.get('chandasColumn')
                        if chandas_col:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                reader = csv.DictReader(f)
                                for row in reader:
                                    if chandas_col in row and row[chandas_col].strip():
                                        unique_chandas_set.add(row[chandas_col].strip())
                unique_chandas = sorted(list(unique_chandas_set))
            else:
                # Single file dataset
                filepath = SOURCE_DIR / ds_data.get('filename', '')
                actual_row_count = 0
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        actual_row_count = sum(1 for _ in f) - 1  # Subtract header

                # Get unique chandas for filtering
                chandas_column = ds_data.get('chandasColumn')
                unique_chandas = []
                if chandas_column:
                    unique_chandas = get_unique_chandas(ds_data.get('filename', ''), chandas_column)

            datasets.append(
                {
                    'id': ds_id,
                    'name': ds_data.get('name', ds_id),
                    'description': ds_data.get('description', ''),
                    'source': ds_data.get('source', 'Unknown'),
                    'sourceReference': ds_data.get('sourceReference', ''),
                    'rowCount': actual_row_count,
                    'dataType': ds_data.get('dataType', 'verses'),
                    'hasSloka': ds_data.get('slokaColumn') is not None,
                    'slokaColumn': ds_data.get('slokaColumn'),
                    'chandasColumn': ds_data.get('chandasColumn'),
                    'patternColumn': ds_data.get('patternColumn'),
                    'patternType': ds_data.get('patternType', 'lg_pattern'),
                    'isMerged': 'files' in ds_data,
                    'uniqueChandas': unique_chandas[:100],  # Limit to first 100 for UI
                }
            )

        # Get all unique sources for filtering
        sources = list(set(ds.get('source') for ds in datasets if ds.get('source')))

        return jsonify(
            {
                'success': True,
                'datasets': datasets,
                'sources': sorted(sources),
                'sourceDescriptions': catalog.get('sourceDescriptions', {}),
            }
        )

    except Exception as e:
        logger.exception(f"Error listing datasets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """
    Get dataset contents with pagination and filtering.

    Query parameters:
        limit: Max rows to return (default: 50, max: 500)
        offset: Rows to skip (default: 0)
        chandas: Filter by chandas name (substring match)

    Returns:
        JSON with dataset rows and metadata
    """
    try:
        catalog = load_dataset_catalog()

        if dataset_id not in catalog.get('datasets', {}):
            return jsonify({'success': False, 'error': f'Dataset not found: {dataset_id}'}), 404

        ds_data = catalog['datasets'][dataset_id]

        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))
        chandas_filter = request.args.get('chandas', '').strip()

        # Handle merged datasets (like iitk_meters)
        if 'files' in ds_data:
            all_rows = []
            all_columns = set()

            for file_info in ds_data['files']:
                filepath = SOURCE_DIR / file_info.get('filename', '')
                if not filepath.exists():
                    continue

                chandas_col = file_info.get('chandasColumn')
                pattern_col = file_info.get('patternColumn')
                category = file_info.get('category', '')

                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    all_columns.update(reader.fieldnames or [])
                    for row in reader:
                        # Add category for merged datasets
                        row['_category'] = category
                        row['_source_file'] = file_info.get('filename', '')

                        # Apply chandas filter if specified
                        if chandas_filter:
                            if chandas_col and chandas_col in row:
                                if chandas_filter.lower() not in row[chandas_col].lower():
                                    continue
                            else:
                                continue

                        all_rows.append(row)

            total_count = len(all_rows)

            # Apply pagination
            paginated_rows = all_rows[offset : offset + limit]

            # Map to standardized format
            chandas_col = ds_data.get('chandasColumn')
            pattern_col = ds_data.get('patternColumn')

            formatted_rows = []
            for row in paginated_rows:
                formatted_row = {
                    'sloka': None,
                    'chandas': row.get(chandas_col, '') if chandas_col else None,
                    'pattern': row.get(pattern_col, '') if pattern_col else None,
                    'source': ds_data.get('source', ''),
                    'category': row.get('_category', ''),
                    'raw': {k: v for k, v in row.items() if not k.startswith('_')},
                }
                formatted_rows.append(formatted_row)

            columns = sorted(list(all_columns))
        else:
            # Single file dataset
            filename = ds_data.get('filename', '')

            # Read data with filters
            rows, total_count, columns = read_csv_data(
                filename, limit=limit, offset=offset, chandas_filter=chandas_filter if chandas_filter else None
            )

            # Map to standardized format
            sloka_col = ds_data.get('slokaColumn')
            chandas_col = ds_data.get('chandasColumn')
            pattern_col = ds_data.get('patternColumn')

            formatted_rows = []
            for row in rows:
                formatted_row = {
                    'sloka': row.get(sloka_col, '') if sloka_col else None,
                    'chandas': row.get(chandas_col, '') if chandas_col else None,
                    'pattern': row.get(pattern_col, '') if pattern_col else None,
                    'source': ds_data.get('source', ''),
                    'category': None,
                    'raw': row,  # Include all original columns
                }
                formatted_rows.append(formatted_row)

        return jsonify(
            {
                'success': True,
                'datasetId': dataset_id,
                'name': ds_data.get('name', dataset_id),
                'description': ds_data.get('description', ''),
                'source': ds_data.get('source', ''),
                'sourceReference': ds_data.get('sourceReference', ''),
                'dataType': ds_data.get('dataType', 'verses'),
                'patternType': ds_data.get('patternType', 'lg_pattern'),
                'columns': columns,
                'slokaColumn': ds_data.get('slokaColumn'),
                'chandasColumn': ds_data.get('chandasColumn'),
                'patternColumn': ds_data.get('patternColumn'),
                'rows': formatted_rows,
                'totalCount': total_count,
                'limit': limit,
                'offset': offset,
                'hasMore': offset + len(formatted_rows) < total_count,
            }
        )

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {e}'}), 400
    except Exception as e:
        logger.exception(f"Error getting dataset {dataset_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/examples', methods=['GET'])
def get_examples():
    """
    Get example verses for testing.

    Returns:
        JSON array of example verses with their meters
    """
    try:
        examples_dict = current_app.chanda.read_examples()

        # Convert dictionary to array format for frontend
        examples_array = []
        for meter_name, content in examples_dict.items():
            if isinstance(content, list):
                # Format: meter_name: [lines...]
                lines = [line for line in content if line.strip()]
                if lines:
                    examples_array.append({'meter': meter_name, 'lines': lines, 'text': '\n'.join(lines)})
            elif isinstance(content, dict):
                # Format: meter_name: {description: ..., examples: [...]}
                if 'examples' in content and isinstance(content['examples'], list):
                    for example_text in content['examples']:
                        examples_array.append(
                            {
                                'meter': meter_name,
                                'text': example_text,
                                'lines': example_text.split('\n'),
                                'description': content.get('description', ''),
                            }
                        )

        return jsonify({'success': True, 'examples': examples_array})
    except Exception as e:
        logger.exception(f"Error loading examples: {e}")
        return jsonify({'success': False, 'error': str(e), 'examples': []}), 500


@bp.route(f'{settings.API_PREFIX}/schemes', methods=['GET'])
def get_schemes():
    """
    Get available transliteration schemes.

    Returns:
        JSON array of available schemes
    """
    schemes = [
        {"value": "", "label": "Match Input"},
        {"value": "devanagari", "label": "Devanagari"},
        {"value": "iast", "label": "IAST"},
        {"value": "itrans", "label": "ITRANS"},
        {"value": "hk", "label": "Harvard-Kyoto"},
        {"value": "wx", "label": "WX"},
        {"value": "slp1", "label": "SLP1"},
        {"value": "assamese", "label": "Assamese"},
        {"value": "bengali", "label": "Bangla"},
        {"value": "gujarati", "label": "Gujarati"},
        {"value": "kannada", "label": "Kannada"},
        {"value": "malayalam", "label": "Malayalam"},
        {"value": "oriya", "label": "Oriya"},
        {"value": "tamil", "label": "Tamil"},
        {"value": "telugu", "label": "Telugu"},
    ]

    return jsonify({'success': True, 'schemes': schemes})
