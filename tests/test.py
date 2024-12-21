''' Test hatch-pyinstaller
'''
import os
from pathlib import Path
from datetime import datetime
from functools import wraps

import humanize

# force path to test package BEFORE importing pyinstaller & hatchling
os.chdir(Path.cwd().joinpath('tests/tst_package'))

from hatchling.cli.build import build_impl  # pylint: disable=wrong-import-position
from PyInstaller import __main__ as PyI     # pylint: disable=wrong-import-position # type: ignore

exec_times = {}
def with_exec_time(func):
    """ decorator to measure & display execution time
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        exec_times[func.__name__] = humanize.precisedelta(end_time - start_time)
        return result
    return wrap

@with_exec_time
def build_hatchling():
    ''' to call hatchling build
    '''
    build_impl(called_by_app = False,
               directory = None,
               targets= ["pyinstaller"],
               hooks_only = None,
               no_hooks = None,
               clean = None,
               clean_hooks_after = None,
               clean_only = False,
               show_dynamic_deps = False)

@with_exec_time
def build_pyinstaller():
    """ To call pyinstaller directly
    """
    PyI.run([
        'foobar.spec',
        # 'src/tst_package/tst.py',
        # '--name=my app',
        # '--add-data=data/Designer.png:.',
        # '--onedir',
        '--noconfirm',
        '--clean',
    ])

if __name__ == "__main__":

    build_hatchling()
    build_pyinstaller()

    for k, v in exec_times.items():
        print(f'>>>>> {k} executed in {v}')
