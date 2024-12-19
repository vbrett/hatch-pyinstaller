import os
import shutil
from zipfile import ZipFile
from pathlib import Path
from typing import Any, Callable
from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
# from hatchling.builders.utils import normalize_relative_path
# I removed relative path normalization, since all path options, including --paths, --add-data & --add-binaries can use absolute paths,
# in which case splitting using ':' fails. Besides, pyinstaller seems very resilient on paths format.
import PyInstaller.__main__ as pyinstaller


class PyInstallerConfig(BuilderConfig):
    def pyinstaller_options(self) -> list[str]:
        """ Extract & format pysintaller options from self.target_config
        """
        option_names = {
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
            "debug",
            "optimize-level",
            "version-file",
            "manifest",
            "osx-bundle-identifier",
            "codesign-identity",
            "osx-entitlements-file",
        }
        build_options = [""] # first element of the list will contain the scriptname and is filled in later on
        build_options.extend(self.target_config["flags"]) # append options with no argument
        # Append options with arguments
        for option, values in self.target_config.items():
            if option in option_names:
                if not isinstance(values, list):
                    values = [values]

                for value in values:
                    build_options.append(f'--{option}={value}')
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

        # extract list of script(s) to build
        scriptnames = self.target_config.get("scriptname", f"{project_name}.py")
        if not isinstance(scriptnames, list):
            scriptnames = [scriptnames]

        # if --distpath is not defined, force it to hatch's dist path
        # instead of using pyinstaller default.
        bundle_dist_path = self.target_config.get("distpath", directory)

        # if --name is defined and multiple scripts are defined,
        # display a warning and delete the field
        if len(scriptnames) > 1 and "name" in self.target_config:
            print("WARNING: setting '--name' pysintaller option is incompatible with having multiple elements in scriptname. Option is ignored")
            self.target_config.pop("name")

        create_zip = self.target_config.get("bundle-as-zip", False)

        # Construct pyinstaller arguments - to do only once all coherency checks are done
        pyinstaller_options = self.config.pyinstaller_options()
        one_file = ("--onefile" in pyinstaller_options or "-F" in pyinstaller_options)

        #TODO cannot support zipping --onedir app
        if create_zip and not one_file:
            print("WARNING: only support zipping --onefile app(s). Zipping is ignored")
            create_zip = False

        for scriptname in scriptnames:
            pyinstaller_options[0] = scriptname
            pyinstaller.run(pyinstaller_options)

        dist_dir = Path(directory, project_name)
        extra_files = []

        if self.metadata.core.readme_path:
            extra_files.append(self.metadata.core.readme_path)
        if self.metadata.core.license_files:
            extra_files.extend(self.metadata.core.license_files)

        if not create_zip:
            for f in extra_files:
                shutil.copy2(f, dist_dir)
        else:
            # zip path & name are based on hatch infos, not pyinstaller's
            zip_filename = Path(directory, project_name + '-' + self.metadata.version + '.bin.zip')
            dist_dir = zip_filename
            with ZipFile(zip_filename, 'w') as zf:
                for scriptname in scriptnames:
                    bundle_filename = self.target_config.get("name", Path(scriptname).stem) + ".exe"
                    created_bundle = Path(bundle_dist_path, bundle_filename)
                    zf.write(created_bundle)
                    #TODO WHY IS IT KEEPING ALL created_bundle PATH ????

                for f in extra_files:
                    zf.write(f)

        return os.fspath(dist_dir)
