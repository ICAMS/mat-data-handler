"""Packaged material data: YAML entries, JSON schemas, and the PROPS mapping.

This package ships data only -- no executable logic. Consumers such as
``mat-data-handler`` (or any other tool) access the bundled files through
:mod:`importlib.resources` so paths resolve correctly whether the package was
installed from a wheel, an sdist, or a conda package.
"""

from importlib import resources

__version__ = "2026.9.0"


def entries_dir():
    """Return a context manager yielding a real filesystem path to entries/."""
    return resources.as_file(resources.files(__package__) / "entries")


def schemas_dir():
    """Return a context manager yielding a real filesystem path to schemas/."""
    return resources.as_file(resources.files(__package__) / "schemas")


def mapping_path():
    """Return a context manager yielding a real filesystem path to mapping.csv."""
    return resources.as_file(resources.files(__package__) / "mapping.csv")
