# -*- coding: utf-8 -*-
"""Data classes and functions related to the app registry configuration.

An app registry can optionally be managed with a configuration file.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Union

from dacite import from_dict

from . import yaml


API_VERSION = "v1"


@dataclass
class DataConfig:
    """Paths to the data files."""

    apps: str
    categories: str


@dataclass
class SchemasConfig:
    """Paths to the schema files."""

    path: str


@dataclass
class EnvironmentsConfig:
    """Configuration on how to determine the environment specification.

    The cmd attribute should contain a shell command, that takes an app
    repository URL as first argument and prints the environment specification
    in JSON format to STDOUT.
    """

    cmd: str


@dataclass
class BuildConfig:
    """Configuration fields related to building the registry website."""

    html: str = "./html"
    static_src: str = None


@dataclass
class Config:
    """The overall app registry configuration."""

    data: DataConfig
    schemas: SchemasConfig
    environments: EnvironmentsConfig
    build: BuildConfig = field(default_factory=BuildConfig)
    api_version: str = "v1"

    @classmethod
    def from_mapping(cls, config_mapping: Mapping):
        """Generate the configuration data class from a mapping, e.g., a dict."""
        _check_api_version(config_mapping.get("api_version"))
        return from_dict(data_class=cls, data=config_mapping)

    @classmethod
    def from_path(cls, config_path: Union[Path, str]):
        """Read the configuration data class from a path pointing to a YAML file."""
        config_yaml = yaml.load(config_path)
        return cls.from_mapping(config_yaml)

    def __post_init__(self):
        _check_api_version(self.api_version)


def _check_api_version(api_version):
    """Check whether the api version of the configuration is supported."""
    if api_version is None:
        raise ValueError("No config api_version provided.")
    elif api_version != API_VERSION:
        raise RuntimeError(
            f"The config api_version ({api_version}) is not supported by this version of the app registry. Consider upgrading."
        )
