"""Create a source-only archive, excluding research code and build dependencies."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

roots = ['app', 'assets', 'docs', 'scripts', 'tests']
files = [Path(name) for name in ['run.py', 'pyproject.toml', 'requirements.txt',
         'requirements-dev.txt', 'requirements-lock.txt', 'README.md',
         'THIRD_PARTY_NOTICES.md', 'packaging/installer.iss']]
for name in roots:
    files.extend(path for path in Path(name).rglob('*') if path.is_file() and '__pycache__' not in path.parts)
with ZipFile('dist/LogiZ407ControlPro-Source.zip', 'w', ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, Path('LogiZ407ControlPro') / path)
