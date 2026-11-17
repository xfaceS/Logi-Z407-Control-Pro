import ctypes
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter

def parse_shortcut(text):
    parts = text.upper().split('+')
    modifiers = 0x4000  # MOD_NOREPEAT
    for part in parts[:-1]:
        modifiers |= {'CTRL': 2, 'ALT': 1, 'SHIFT': 4, 'META': 8}[part]
    key = {'UP': 0x26, 'DOWN': 0x28, 'LEFT': 0x25, 'RIGHT': 0x27}.get(parts[-1])
    if key is None:
        if len(parts[-1]) != 1 or not parts[-1].isalnum():
            raise ValueError('Use Ctrl/Alt/Shift/Meta with a letter, digit or arrow.')
        key = ord(parts[-1])
    if modifiers == 0x4000:
        raise ValueError('At least one modifier is required.')
    return modifiers, key

class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.registered = {}

    def clear(self):
        for identifier in self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, identifier)
        self.registered.clear()

    def configure(self, keys):
        self.clear()
        try:
            for identifier, (action, text) in enumerate(keys.items(), 1):
                modifiers, key = parse_shortcut(text)
                if not ctypes.windll.user32.RegisterHotKey(None, identifier, modifiers, key):
                    raise ValueError(f'Shortcut unavailable or already registered: {text}')
                self.registered[identifier] = action
        except Exception:
            self.clear()
            raise

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x0312 and msg.wParam in self.registered:
            self.callback(self.registered[msg.wParam])
            return True, 0
        return False, 0
