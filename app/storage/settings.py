import json
import os
from pathlib import Path
import tempfile

DEFAULTS = {'theme': 'Dark', 'tray': True, 'auto_connect': False, 'reconnect': True,
            'preferred': '', 'shortcuts': False,
            'keys': {'VOLUME_UP': 'Ctrl+Alt+Up', 'VOLUME_DOWN': 'Ctrl+Alt+Down',
                     'BASS_UP': 'Ctrl+Alt+Right', 'BASS_DOWN': 'Ctrl+Alt+Left'},
            'presets': {'Deep Bass': 3, 'Balanced': 0, 'Music': 1, 'Gaming': 2, 'Movies': 2, 'Night Mode': -2}}

class Settings:
    def __init__(self, path=None):
        self.path = Path(path or Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'LogiZ407ControlPro' / 'settings.json')
        self.data = json.loads(json.dumps(DEFAULTS))
        self.error = None
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding='utf-8'))
                for key, value in loaded.items():
                    if key in DEFAULTS and isinstance(value, type(DEFAULTS[key])):
                        self.data[key] = value
            except (ValueError, OSError) as exc:
                self.error = str(exc)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=self.path.parent, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(self.data, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
