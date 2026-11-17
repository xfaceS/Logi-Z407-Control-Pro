import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app.services import Worker
from app.storage.settings import Settings
from app.ui.window import Window
import asyncio

def test_native_window_tray_and_shutdown(tmp_path):
    application = QApplication.instance() or QApplication([])
    settings = Settings(tmp_path / 'settings.json')
    worker = Worker()
    window = Window(worker, settings, QIcon())
    window.show()
    application.processEvents()
    assert window.pages.count() == 6
    assert all(not widget.isEnabled() for widget in window.hardware_widgets)
    assert window.tray.contextMenu().actions()[-1].text() == 'Exit'
    window.on_event('command', 'BASS_UP')
    assert window.state.bass == 1
    window.on_event('ready', False)
    assert not window.state.calibrated
    window.quit()
    worker.shutdown()
    assert not worker.thread.is_alive()

def test_shutdown_cancels_inflight_work():
    application = QApplication.instance() or QApplication([])
    worker = Worker()
    future = worker.submit(asyncio.sleep(60))
    worker.shutdown()
    assert future.done()
    assert not worker.thread.is_alive()

