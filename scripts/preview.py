import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer
from app.services import Worker
from app.storage.settings import Settings
from app.ui.window import Window

application = QApplication([])
worker = Worker()
settings = Settings(Path('build/preview-settings.json'))
window = Window(worker, settings, QIcon('assets/app.ico'))
window.show()
def capture():
    window.grab().save('docs/dashboard.png')
    window.quit()
QTimer.singleShot(500, capture)
application.exec()
worker.shutdown()
