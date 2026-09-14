"""Public API: validate/combine material YAML entries and export Abaqus .inc files.

See :mod:`mat_data_handler.database` for building the combined database and
:mod:`mat_data_handler.extract` for exporting selected materials to Abaqus
``PROPS`` include files.
"""

from importlib import metadata

try:
    __version__ = metadata.version("mat-data-handler")
except metadata.PackageNotFoundError:  # local checkout, not installed
    __version__ = "0.0.0+dev"

from .database import build_database, collect, validate_only
from .extract import export_material

__all__ = ["build_database", "collect", "validate_only", "export_material", "__version__"]
