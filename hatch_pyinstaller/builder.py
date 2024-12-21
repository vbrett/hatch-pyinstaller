import os
import shutil
import zipfile
from pathlib import Path
import tempfile

from typing import Any, Callable
from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import normalize_relative_path
import PyInstaller.__main__ as pyinstaller


class PyInstallerConfig(BuilderConfig):
    def pyinstaller_options(self) -> list[str]:
        path_options_single = (
            "distpath",
            "workpath",
            "upx-dir",
            "specpath",
            "name",
            "contents-directory",
            "paths",
            "icon",
            "splash",
            "upx-exclude",
            "runtime-tmpdir",
        )
        path_options_multi = (
            "add-data",
            "add-binary",
            "hidden-import",
            "collect-submodules",
            "collect-data",
            "collect-binaries",
            "collect-all",
            "copy-metadata",
            "recursive-copy-metadata",
            "additional-hooks-dir",
            "runtime-hook",
            "exclude-module",
        )
        other = (
            "debug",
            "optimize-level",
            "version-file",
            "manifest",
            "osx-bundle-identifier",
            "codesign-identity",
            "osx-entitlements-file",
        )
        build_options = []
        build_options.append("")
        build_options.extend(self.target_config["flags"])
        for option in self.target_config:
            if option in path_options_single:
                if option == "paths":
                    paths = self.target_config[option].split(":")
                    paths = [p for p in map(normalize_relative_path, paths)]
                    build_options.extend(["--paths", ":".join(paths)])
                else:
                    build_options.extend(
                        [
                            f"--{option}",
                            normalize_relative_path(self.target_config[option]),
                        ]
                    )
            elif option in path_options_multi:
                for value in self.target_config[option]:
                    if option in ("add-data", "add-binary"):
                        src, dst = value.split(":")
                        value = f"{normalize_relative_path(src)}:{normalize_relative_path(dst)}"
                        build_options.extend([f"--{option}", value])
                    else:
                        build_options.extend(
                            [
                                f"--{option}",
                                normalize_relative_path(value),
                            ]
                        )
            elif option in other:
                build_options.extend([f"--{option}", self.target_config[option]])
        return build_options

class PyInstallerBuilder(BuilderInterface):
    PLUGIN_NAME = "pyinstaller"

    @classmethod
    def get_config_class(cls) -> BuilderConfig:
        return PyInstallerConfig

    def get_version_api(self) -> dict[str, Callable[..., Any]]:
        return {"app": self.build_app}

    def build_app(self, directory: str, **_build_data: Any) -> str:
        project_name = self.normalize_file_name_component(self.metadata.core.raw_name)

        # extract list of script(s) to build and ensure to have it as a list
        scriptnames = self.target_config.get("scriptname", f"{project_name}.py")
        if not isinstance(scriptnames, list):
            scriptnames = [scriptnames]

        # when zipping, use a temp directory as distpath
        create_zip = self.target_config.get("zip", False)
        if create_zip:
            temp_dir = tempfile.TemporaryDirectory()
            if "distpath" in self.target_config:
            # --distpath option is not compatible with zipping bundles. Display a warning.
                print("WARNING: '--distpath' option is incompatible with zipping bundles. Option is ignored.")
            self.target_config["distpath"] = temp_dir.name
        else:
            # if --distpath is not defined, force it to hatch's dist path instead of using pyinstaller default.
            _dont_care = self.target_config.get("distpath", directory)

        # --name option is not compatible with bundling multiple scripts. Display a warning and delete the field.
        if len(scriptnames) > 1 and "name" in self.target_config:
            print("WARNING: '--name' option is incompatible with bundling multiple scriptnames. Option is ignored.")
            self.target_config.pop("name")

        # Construct pyinstaller arguments - to do only once all coherency checks are done
        pyinstaller_options = self.config.pyinstaller_options()

        for scriptname in scriptnames:
            pyinstaller_options[0] = scriptname
            pyinstaller.run(pyinstaller_options)

        extra_files = []
        if self.metadata.core.readme_path:
            extra_files.append(self.metadata.core.readme_path)
        if self.metadata.core.license_files:
            extra_files.extend(self.metadata.core.license_files)

        if not create_zip:
            package_path = Path(directory, project_name)
            for f in extra_files:
                shutil.copy2(f, package_path)
        else:
            # zip is located in hatch dist, zip name mimics wheel & sdist naming rules
            package_path = Path(directory, project_name + '-' + self.metadata.version + '.bin.zip')
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _dirs, files in os.walk(Path(temp_dir.name), topdown = False):
                    for name in files:
                        zipped_file = Path(root, name)
                        zf.write(zipped_file, zipped_file.relative_to(temp_dir.name))

                for f in extra_files:
                    zf.write(f, Path(f).name)

        return os.fspath(package_path)
