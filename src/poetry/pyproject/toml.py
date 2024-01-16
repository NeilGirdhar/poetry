from __future__ import annotations

from typing import TYPE_CHECKING

from poetry.core.pyproject.toml import PyProjectTOML as BasePyProjectTOML
from tomlkit.api import table
from tomlkit.items import Table, Item
from tomlkit.toml_document import TOMLDocument

from poetry.toml import TOMLFile


if TYPE_CHECKING:
    from pathlib import Path


def apply_overrides(result: TOMLDocument, overrides: TOMLDocument) -> None:
    for key in overrides:
        if key not in result:
            result.append(key, overrides[key])
        else:
            if isinstance(overrides[key], Item):
                result.remove(key)
                result.append(key, overrides[key])
            else:
                apply_overrides(result[key], overrides[key])


class PyProjectTOML(BasePyProjectTOML):
    """
    Enhanced version of poetry-core's PyProjectTOML
    which is capable of writing pyproject.toml

    The poetry-core class uses tomli to read the file,
    here we use tomlkit to preserve comments and formatting when writing.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self._toml_file = TOMLFile(path=path)
        override_path = path.with_name('override.toml')
        self._override_file = TOMLFile(path=override_path)
        self._toml_document: TOMLDocument | None = None

    @property
    def file(self) -> TOMLFile:
        return self._toml_file

    @property
    def override_file(self) -> TOMLFile:
        return self._override_file

    @property
    def data(self) -> TOMLDocument:
        if self._toml_document is None:
            if not self.file.exists():
                self._toml_document = TOMLDocument()
            else:
                result = self.file.read()
                if self.override_file.exists():
                    overrides = self.override_file.read()
                    apply_overrides(result, overrides)
                self._toml_document = result

        return self._toml_document

    def save(self) -> None:
        data = self.data

        if self._build_system is not None:
            if "build-system" not in data:
                data["build-system"] = table()

            build_system = data["build-system"]
            assert isinstance(build_system, Table)

            build_system["requires"] = self._build_system.requires
            build_system["build-backend"] = self._build_system.build_backend

        self.file.write(data=data)

    def reload(self) -> None:
        self._toml_document = None
        self._build_system = None
