"""Retain installed dependency licenses alongside the redistributable."""
from importlib.metadata import distributions
from pathlib import Path
import shutil
import sys

destination = Path(sys.argv[1] if len(sys.argv) > 1 else 'dist/LogiZ407ControlPro/licenses')
destination.mkdir(parents=True, exist_ok=True)
for license_path in Path('assets/licenses').glob('*.txt'):
    shutil.copy2(license_path, destination / license_path.name)
for package in distributions():
    for entry in package.files or []:
        if ('licenses' in [part.lower() for part in entry.parts] or
                any(word in entry.name.lower() for word in ('license', 'copying', 'copyright', 'lgpl', 'gpl'))):
            source = Path(package.locate_file(entry))
            if source.is_file():
                target = destination / package.metadata['Name'] / str(entry).replace('../', '').replace('..\\', '')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
