"""Keep Windows' OS ICU instead of a conflicting DLL inherited from build PATH."""
from pathlib import Path
import shutil

root = Path('dist/LogiZ407ControlPro/_internal').resolve()
assert root.is_relative_to(Path('dist').resolve())
# Qt's Windows build imports unsuffixed ICU symbols provided by system32/icuuc.dll.
# A builder's PATH can contain a different ICU with version-suffixed exports.
for name in ('icuuc.dll', 'icudt78.dll'):
    path = root / name
    if path.exists(): path.unlink()
# Qt ships a matching Microsoft runtime. Prefer it to Python's older copy.
for path in (root / 'PySide6').glob('*140*.dll'):
    shutil.copy2(path, root / path.name)
