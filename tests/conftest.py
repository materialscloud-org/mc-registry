import json
from functools import partial
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).parent.parent.resolve()


@pytest.fixture
def validate():
    return partial(jsonschema.validate, format_checker=jsonschema.draft7_format_checker)


@pytest.fixture
def apps_schema():
    return json.loads(ROOT.joinpath("schemas/apps.schema.json").read_text())


@pytest.fixture
def apps_meta_schema():
    return json.loads(ROOT.joinpath("schemas/apps_meta.schema.json").read_text())


@pytest.fixture
def categories_schema():
    return json.loads(ROOT.joinpath("schemas/categories.schema.json").read_text())


@pytest.fixture
def metadata_schema():
    return json.loads(ROOT.joinpath("schemas/metadata.schema.json").read_text())


@pytest.fixture
def mock_schema_endpoints(
    requests_mock, apps_schema, apps_meta_schema, categories_schema, metadata_schema
):
    requests_mock.get(
        "https://aiidalab.github.io/aiidalab-registry/schemas/v2/apps.schema.json",
        text=json.dumps(apps_schema),
    )
    requests_mock.get(
        "https://aiidalab.github.io/aiidalab-registry/schemas/v2/metadata.schema.json",
        text=json.dumps(metadata_schema),
    )
    requests_mock.get(
        "https://aiidalab.github.io/aiidalab-registry/schemas/v2/apps_meta.schema.json",
        text=json.dumps(apps_meta_schema),
    )
    requests_mock.get(
        "https://aiidalab.github.io/aiidalab-registry/schemas/v2/categories.schema.json",
        text=json.dumps(categories_schema),
    )


@pytest.fixture
def mock_hello_world_app_metadata_endpoint(requests_mock):
    requests_mock.get(
        "https://raw.githubusercontent.com/aiidalab/aiidalab-hello-world/apps-registry-schema-v2/metadata.json",
        text="""
{
    "title": "Hello World App",
    "description": "This is an AiiDA lab hello world app created with the aiidalab-app-cutter.",
    "authors": "The AiiDA lab Team",
    "logo": "img/logo.png",
    "state": "development"
}
        """,
    )