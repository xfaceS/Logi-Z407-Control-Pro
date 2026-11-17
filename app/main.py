import os
import sys
from pathlib import Path
from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from app.services import Worker
from app.storage.settings import Settings
from app.ui.window import Window

def main():
    if '--ble-scan-report' in sys.argv:
        import asyncio
        import json
        from app.bluetooth.controller import Controller
        target = Path(sys.argv[sys.argv.index('--ble-scan-report') + 1])
        report = {'events': []}
        def capture(kind, value):
            if kind == 'devices': report['devices_found'] = len(value)
            else: report['events'].append([kind, str(value)])
        asyncio.run(Controller(capture).scan())
        target.write_text(json.dumps(report, indent=2), encoding='utf-8')
        return 1 if any(kind == 'error' for kind, _ in report['events']) else 0
    application = QApplication(sys.argv)
    application.setApplicationName('Logi Z407 Control Pro')
    application.setOrganizationName('LogiZ407ControlPro')
    settings = Settings()
    settings.path.parent.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(settings.path.parent / 'app.lock'))
    if not lock.tryLock(100):
        if '--smoke-test' not in sys.argv:
            QMessageBox.information(None, 'Already running', 'Logi Z407 Control Pro is already running. Open it from the system tray.')
        return 2
    resources = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    icon = QIcon(str(resources / 'assets' / 'app.ico'))
    worker = Worker()
    window = Window(worker, settings, icon)
    window.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(1500, window.quit)
    try:
        return application.exec()
    finally:
        window.hotkeys.clear()
        worker.shutdown()
        lock.unlock()

if __name__ == '__main__':
    raise SystemExit(main())
