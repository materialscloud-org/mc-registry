import re
from dataclasses import asdict
from pathlib import Path

import jsonschema
import pytest

from app_registry import yaml

ROOT = Path(__file__).parent.parent.resolve()


@pytest.fixture
def apps_yaml():
    return yaml.load(ROOT.joinpath("apps.yaml"))


@pytest.fixture
def categories_yaml():
    return yaml.load(ROOT.joinpath("categories.yaml"))


@pytest.fixture
def valid_categories(categories_yaml):
    return set(categories_yaml)


def test_validate_schemas(schemas):
    for schema in asdict(schemas).values():
        jsonschema.Draft7Validator.check_schema(schema)


@pytest.mark.usefixtures("mock_schema_endpoints")
def test_validate_apps_yaml_schema(
    requests_mock, apps_yaml, validate, schemas, valid_categories
):
    matcher = re.compile(r"\/metadata\.json$")
    requests_mock.register_uri("GET", matcher, real_http=True)
    validate(instance=apps_yaml, schema=schemas.apps)


@pytest.mark.usefixtures("mock_schema_endpoints")
def test_validate_apps_yaml_categories(apps_yaml, valid_categories):
    for app in apps_yaml.values():
        for category in app.get("categories", []):
            assert category in valid_categories


@pytest.mark.usefixtures("mock_schema_endpoints")
def test_validate_categories_yaml(validate, schemas, categories_yaml):
    validate(instance=categories_yaml, schema=schemas.categories)
