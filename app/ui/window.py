import json
import re
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QStackedWidget, QFrame, QDial, QSlider,
    QSystemTrayIcon, QMenu, QCheckBox, QFileDialog, QMessageBox, QPlainTextEdit,
    QInputDialog, QLineEdit, QFormLayout, QApplication)
from ..bluetooth.protocol import Command
from ..profiles import RelativeState
from ..audio.windows import WindowsAudio
from .hotkeys import Hotkeys

def button(text, callback):
    widget = QPushButton(text)
    widget.clicked.connect(callback)
    widget.setMinimumHeight(36)
    return widget

def label(text, size=11, color=None):
    widget = QLabel(text)
    widget.setWordWrap(True)
    widget.setFont(QFont('Segoe UI', size))
    widget.setStyleSheet(f'font-size:{size}pt; background:transparent;' + (f'color:{color};' if color else ''))
    return widget

class StepDial(QDial):
    """Endless relative dial: each movement requests a single real hardware step."""
    def __init__(self, callback):
        super().__init__()
        self.setRange(-50, 50)
        self.setValue(0)
        self.setNotchesVisible(True)
        self.setFixedSize(160, 160)
        self.previous = 0
        self.valueChanged.connect(lambda value: self.change(value, callback))
        self.sliderReleased.connect(self.reset)

    def change(self, value, callback):
        delta = value - self.previous
        self.previous = value
        if delta:
            callback(delta > 0)

    def reset(self):
        self.blockSignals(True)
        self.setValue(0)
        self.previous = 0
        self.blockSignals(False)

class Window(QMainWindow):
    def __init__(self, worker, settings, icon):
        super().__init__()
        self.worker, self.settings = worker, settings
        self.state = RelativeState()
        self.quitting = False
        self.hardware_widgets = []
        self.preset_busy = False
        self.records = []
        self.setWindowTitle('Logi Z407 Control Pro')
        self.setWindowIcon(icon)
        self.resize(1110, 800)
        self.setMinimumSize(810, 650)
        self.audio = WindowsAudio()
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        self.nav = QListWidget()
        self.nav.setFixedWidth(184)
        self.nav.addItems(['Dashboard', 'Speaker Control', 'Bass & Profiles', 'Audio & Media', 'Remote Access', 'Diagnostics', 'Settings'])
        layout.addWidget(self.nav)
        body = QVBoxLayout()
        layout.addLayout(body, 1)
        body.addWidget(label('LOGI  /  Z407 CONTROL PRO', 20, '#65cee0'))
        self.status = label('Disconnected · scan to find your speaker', 11)
        body.addWidget(self.status)
        row = QHBoxLayout()
        self.devices = QComboBox()
        self.devices.setMinimumWidth(200)
        row.addWidget(self.devices, 1)
        row.addWidget(button('Scan', self.scan))
        row.addWidget(button('Connect', self.connect_device))
        row.addWidget(button('Disconnect', lambda: self.worker.submit(self.worker.controller.disconnect())))
        body.addLayout(row)
        self.input_label = label('Input: unknown', 10, '#a5b5c5')
        body.addWidget(self.input_label)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        self.nav.currentRowChanged.connect(self.navigate)
        self.dashboard()
        self.profiles_page()
        self.audio_page()
        self.remote_page()
        self.diagnostics_page()
        self.settings_page()
        self.nav.setCurrentRow(0)
        self.worker.event.connect(self.on_event)
        self.hotkeys = Hotkeys(self.hotkey)
        QApplication.instance().installNativeEventFilter(self.hotkeys)
        self.make_tray(icon)
        self.set_ready(False)
        self.theme()
        self.refresh_audio()
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.refresh_audio)
        self.audio_timer.start(5000)
        if settings.data['shortcuts']:
            self.configure_hotkeys()
        if settings.error:
            self.on_event('error', 'Settings could not be read: ' + settings.error)
        worker.controller.auto_reconnect = settings.data['reconnect']
        if settings.data['auto_connect'] and settings.data['preferred']:
            QTimer.singleShot(300, lambda: worker.submit(worker.controller.connect(settings.data['preferred'])))

    def page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        self.pages.addWidget(widget)
        return layout

    def hw_button(self, text, command):
        widget = button(text, lambda: self.send(command))
        self.hardware_widgets.append(widget)
        return widget

    def dashboard(self):
        page = self.page()
        page.addWidget(label('Direct speaker control', 18))
        row = QHBoxLayout()
        self.volume_label = label('0 steps this session', 12)
        self.bass_label = label('0 steps this session', 12)
        for title, value, up, down in [('SPEAKER VOLUME', self.volume_label, Command.VOLUME_UP, Command.VOLUME_DOWN),
                                       ('HARDWARE BASS', self.bass_label, Command.BASS_UP, Command.BASS_DOWN)]:
            frame = QFrame()
            frame.setObjectName('panel')
            column = QVBoxLayout(frame)
            column.addWidget(label(title, 11, '#65cee0'))
            dial = StepDial(lambda positive, u=up, d=down: self.send(u if positive else d))
            dial.setAccessibleName(title + ' relative adjustment')
            self.hardware_widgets.append(dial)
            column.addWidget(dial, alignment=Qt.AlignCenter)
            value.setAlignment(Qt.AlignCenter)
            column.addWidget(value)
            controls = QHBoxLayout()
            controls.addWidget(self.hw_button('−  Decrease', down))
            controls.addWidget(self.hw_button('+  Increase', up))
            column.addLayout(controls)
            row.addWidget(frame)
        page.addLayout(row)
        page.addWidget(label('Session counts are acknowledged adjustments, not measured levels. Saturation and physical dial changes can make estimates inaccurate.', 10, '#a5b5c5'))
        inputs = QHBoxLayout()
        for name in ('BLUETOOTH', 'USB', 'AUX'):
            inputs.addWidget(self.hw_button('Bluetooth' if name == 'BLUETOOTH' else name, Command[name]))
        page.addLayout(inputs)
        media = QHBoxLayout()
        for text, action in [('PC Previous', 'previous'), ('PC Play / Pause', 'play'), ('PC Next', 'next')]:
            media.addWidget(button(text, lambda checked=False, a=action: self.audio_action(lambda: self.audio.media(a))))
        media.addWidget(button('Windows Mute', lambda: self.audio_action(self.audio.mute)))
        page.addLayout(media)
        self.summary_audio = label('Windows audio: querying…', 10)
        page.addWidget(self.summary_audio)
        compact = QHBoxLayout()
        compact.addWidget(button('Compact controls', self.compact))
        compact.addWidget(button('Bass profiles →', lambda: self.nav.setCurrentRow(2)))
        page.addLayout(compact)
        page.addStretch()

    def profiles_page(self):
        page = self.page()
        page.addWidget(label('Bass & Profiles', 22))
        page.addWidget(label('Profiles are offsets from a bass baseline you establish by listening. The protocol cannot read an absolute bass level. No sweep to minimum or maximum is performed.'))
        self.baseline = label('Baseline not established', 14, '#65cee0')
        page.addWidget(self.baseline)
        page.addWidget(button('Use current bass as my baseline', self.calibrate))
        page.addWidget(button('Invalidate baseline after physical dial use', self.invalidate))
        self.preset = QComboBox()
        self.preset.addItems(self.settings.data['presets'])
        page.addWidget(self.preset)
        page.addWidget(button('Apply selected offset…', self.apply_preset))
        page.addWidget(button('Save custom bass offset…', self.save_preset))
        page.addWidget(label('Preset names are editable preferences, not Logitech tuning curves. Re-establish your baseline after reconnection, physical dial use, or any uncertain command. Each application is limited to six steps.'))
        page.addWidget(label('Software EQ · unavailable', 16))
        page.addWidget(label('Hardware bass works directly on the speaker. System-wide software EQ needs a separate compatible audio-processing engine. No driver is installed and no ineffective EQ sliders are shown.'))
        page.addStretch()

    def audio_page(self):
        page = self.page()
        page.addWidget(label('Windows audio & media', 22))
        self.audio_name = label('')
        page.addWidget(self.audio_name)
        self.master = QSlider(Qt.Horizontal)
        self.master.setRange(0, 100)
        self.master.setAccessibleName('Windows master volume')
        self.master.sliderReleased.connect(lambda: self.audio_action(lambda: self.audio.volume(self.master.value())))
        page.addWidget(self.master)
        page.addWidget(button('Mute / unmute Windows', lambda: self.audio_action(self.audio.mute)))
        page.addWidget(label('Active playback outputs', 14))
        self.outputs = QListWidget()
        self.outputs.setMaximumHeight(100)
        page.addWidget(self.outputs)
        self.session_box = QVBoxLayout()
        page.addLayout(self.session_box)
        page.addWidget(button('Refresh outputs & app sessions', self.refresh_audio_sessions))
        page.addWidget(label('Media buttons on the dashboard send Windows multimedia keys to the active media application. Track metadata is not available in this version. Speaker playback commands below control the Bluetooth source only.', 10))
        row = QHBoxLayout()
        for name in ('PREVIOUS', 'PLAY_PAUSE', 'NEXT'):
            row.addWidget(self.hw_button('Speaker ' + name.replace('_', ' ').title(), Command[name]))
        page.addLayout(row)
        page.addStretch()

    def remote_page(self):
        page = self.page()
        page.addWidget(label('Remote access', 22))
        page.addWidget(label('Disabled · no network listener', 16, '#65cee0'))
        page.addWidget(label('Mobile LAN control is not included in this release. Secure per-device authorization, pairing and token revocation must be completed before LAN access is enabled. The desktop application makes no cloud connections.'))
        page.addStretch()

    def diagnostics_page(self):
        page = self.page()
        page.addWidget(label('Diagnostics', 22))
        page.addWidget(label('Version 0.1.0 · WinRT BLE · acknowledgment-based command tracking. Scan checks adapter access; GATT and handshake results appear below. See docs/TESTING.md for hardware transport results and remaining listening tests.'))
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        page.addWidget(self.log)
        page.addWidget(button('Export redacted diagnostic report', self.export_diagnostics))

    def settings_page(self):
        page = self.page()
        page.addWidget(label('Settings', 22))
        self.theme_select = QComboBox()
        self.theme_select.addItems(['Dark', 'Light'])
        self.theme_select.setCurrentText(self.settings.data['theme'])
        self.theme_select.currentTextChanged.connect(self.change_theme)
        page.addWidget(self.theme_select)
        for key, title in [('tray', 'Close window to tray'), ('auto_connect', 'Connect to preferred device on launch'), ('reconnect', 'Retry unexpected disconnection (maximum five attempts)'), ('shortcuts', 'Enable global shortcuts')]:
            check = QCheckBox(title)
            check.setChecked(self.settings.data[key])
            check.toggled.connect(lambda checked, k=key: self.set_setting(k, checked))
            page.addWidget(check)
        self.key_fields = {}
        form = QFormLayout()
        for action, text in self.settings.data['keys'].items():
            edit = QLineEdit(text)
            self.key_fields[action] = edit
            form.addRow(action.replace('_', ' ').title(), edit)
        page.addLayout(form)
        page.addWidget(button('Save shortcut configuration', self.save_keys))
        page.addWidget(button('Export preferences', self.export_settings))
        page.addWidget(label('Language: English. Windows startup can be configured using the installer’s optional startup shortcut. Preferences and diagnostics remain on this PC.'))
        page.addStretch()

    def navigate(self, index):
        self.pages.setCurrentIndex({0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}[index])
        if index == 3: self.refresh_audio_sessions()

    def scan(self):
        self.worker.submit(self.worker.controller.scan())

    def connect_device(self):
        device = self.devices.currentData()
        if not device:
            self.on_event('error', 'No device selected. Scan first. If the dial owns the speaker, remove its batteries or leave it idle for five minutes. Audio pairing and BLE remote control are separate connections.')
            return
        self.settings.data['preferred'] = device.address
        self.persist()
        self.worker.submit(self.worker.controller.connect(device))

    def send(self, command):
        if self.preset_busy:
            self.on_event('error', 'Wait for the current bass profile adjustment to finish.')
            return
        self.worker.submit(self.worker.controller.send(command))

    def hotkey(self, action):
        if action in Command.__members__: self.send(Command[action])

    def on_event(self, kind, value):
        if kind == 'preset_done':
            self.preset_busy = False
            return
        if kind != 'notification':
            line = f'{datetime.now().isoformat(timespec="seconds")}  {kind}: {value}'
            line = re.sub(r'(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', '[device]', line)
            self.records.append(line)
            self.records = self.records[-500:]
            self.log.appendPlainText(line)
        if kind in ('state', 'error'):
            self.status.setText(str(value))
            if kind == 'error': self.invalidate()
        elif kind == 'ready': self.set_ready(value)
        elif kind == 'input': self.input_label.setText('Input: ' + value)
        elif kind == 'devices':
            self.devices.clear()
            for device in value:
                self.devices.addItem(f'{device.name or "Z407"} · …{device.address[-5:]}', device)
        elif kind == 'command':
            self.state.apply(value)
            self.volume_label.setText(f'{self.state.volume:+d} steps this session')
            self.bass_label.setText(f'{self.state.bass:+d} steps from baseline' if self.state.calibrated else f'{self.state.bass:+d} steps this session')

    def set_ready(self, ready):
        for widget in self.hardware_widgets: widget.setEnabled(ready)
        if not ready: self.invalidate()

    def invalidate(self):
        self.state.invalidate()
        self.baseline.setText('Baseline not established')
        self.volume_label.setText('0 steps this session · level unknown')
        self.bass_label.setText('0 steps this session · level unknown')

    def calibrate(self):
        if self.preset_busy or self.worker.controller.pending:
            self.on_event('error', 'Wait for pending adjustments before establishing a baseline.')
            return
        if not self.worker.controller.ready:
            self.on_event('error', 'Connect before establishing a baseline.')
            return
        if QMessageBox.question(self, 'Manual bass baseline', 'Have you adjusted the speaker bass to your preferred reference by listening? This records the current level as relative zero; it does not measure or change bass.') == QMessageBox.Yes:
            self.state.establish_baseline()
            self.baseline.setText('Manual baseline established · estimate only')
            self.bass_label.setText('0 steps from manual baseline')

    def apply_preset(self):
        if self.preset_busy: return
        try:
            target = self.settings.data['presets'][self.preset.currentText()]
            delta = self.state.preset_delta(target)
            if not self.worker.controller.ready: raise ValueError('Speaker is disconnected.')
        except (ValueError, KeyError) as exc:
            self.on_event('error', str(exc))
            return
        if not delta: return
        if QMessageBox.question(self, 'Apply relative bass offset', f'Send {abs(delta)} bass {"up" if delta > 0 else "down"} steps? This assumes no physical dial adjustments since calibration.') != QMessageBox.Yes:
            return
        self.preset_busy = True
        generation = self.worker.controller.generation
        async def apply():
            try:
                for _ in range(abs(delta)):
                    if generation != self.worker.controller.generation:
                        raise RuntimeError('Profile stopped after connection changed. Re-establish the bass baseline.')
                    await self.worker.controller.send(Command.BASS_UP if delta > 0 else Command.BASS_DOWN)
            finally:
                self.worker.event.emit('preset_done', True)
        self.worker.submit(apply())

    def save_preset(self):
        name, ok = QInputDialog.getText(self, 'Custom profile', 'Profile name:')
        if not ok or not name.strip(): return
        offset, ok = QInputDialog.getInt(self, 'Bass offset', 'Steps from manual baseline:', 0, -6, 6)
        if ok:
            self.settings.data['presets'][name.strip()[:60]] = offset
            self.persist()
            self.preset.clear()
            self.preset.addItems(self.settings.data['presets'])

    def audio_action(self, callback):
        try:
            callback()
            self.refresh_audio()
        except Exception as exc: self.on_event('error', f'Windows audio unavailable: {exc}')

    def refresh_audio(self):
        try:
            default = self.audio.api.GetSpeakers()
            endpoint = default.EndpointVolume
            volume = round(endpoint.GetMasterVolumeLevelScalar() * 100)
            text = f'{default.FriendlyName} · {volume}% Windows volume' + (' · muted' if endpoint.GetMute() else '')
            self.audio_name.setText(text)
            self.summary_audio.setText(text)
            if not self.master.isSliderDown(): self.master.setValue(volume)
        except Exception as exc:
            self.audio_name.setText('Windows audio unavailable: ' + str(exc))
            self.summary_audio.setText(self.audio_name.text())

    def refresh_audio_sessions(self):
        try:
            default, devices, sessions = self.audio.snapshot()
            self.outputs.clear()
            for device in devices:
                self.outputs.addItem(f'{device.FriendlyName}' + (' · default' if device.id == default.id else ''))
            while self.session_box.count():
                item = self.session_box.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            for session in sessions:
                name = session.Process.name() if session.Process else session.DisplayName or 'System sounds'
                row = QWidget()
                layout = QHBoxLayout(row)
                layout.addWidget(label(name), 1)
                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, 100)
                slider.setValue(round(session.SimpleAudioVolume.GetMasterVolume() * 100))
                slider.setAccessibleName(name + ' application volume')
                slider.sliderReleased.connect(lambda s=slider, v=session.SimpleAudioVolume: self.audio_action(lambda: v.SetMasterVolume(s.value()/100, None)))
                layout.addWidget(slider, 1)
                self.session_box.addWidget(row)
        except Exception as exc: self.on_event('error', 'Audio session enumeration: ' + str(exc))

    def persist(self):
        try: self.settings.save()
        except OSError as exc: self.on_event('error', 'Settings save failed: ' + str(exc))

    def set_setting(self, key, value):
        self.settings.data[key] = value
        self.persist()
        if key == 'reconnect': self.worker.controller.auto_reconnect = value
        if key == 'shortcuts': self.configure_hotkeys()

    def save_keys(self):
        self.settings.data['keys'] = {action: edit.text() for action, edit in self.key_fields.items()}
        self.configure_hotkeys()
        self.persist()

    def configure_hotkeys(self):
        self.hotkeys.clear()
        if self.settings.data['shortcuts']:
            try: self.hotkeys.configure(self.settings.data['keys'])
            except (ValueError, KeyError) as exc: self.on_event('error', str(exc))

    def change_theme(self, value):
        self.settings.data['theme'] = value
        self.persist()
        self.theme()

    def theme(self):
        dark = self.settings.data['theme'] == 'Dark'
        bg, panel, fg, border = ('#14191f', '#1e252e', '#edf2f7', '#35414d') if dark else ('#eef2f5', '#ffffff', '#18212b', '#c2cdd7')
        self.setStyleSheet(f'''
            QWidget {{ background:{bg}; color:{fg}; font-family:'Segoe UI'; font-size:13px; }}
            QFrame#panel {{ background:{panel}; border:1px solid {border}; border-radius:8px; }}
            QPushButton, QComboBox, QLineEdit {{ background:{panel}; border:1px solid {border}; border-radius:5px; padding:7px 12px; }}
            QPushButton:hover {{ border-color:#65cee0; }}
            QPushButton:disabled, QDial:disabled {{ color:#687482; }}
            QListWidget {{ border:none; background:{panel}; padding:8px; }}
            QListWidget::item {{ padding:12px 6px; }}
            QListWidget::item:selected {{ background:#254856; color:#c4f6ff; border-radius:4px; }}
            QSlider::groove:horizontal {{ height:5px; background:{border}; }}
            QSlider::handle:horizontal {{ width:15px; margin:-5px 0; border-radius:7px; background:#65cee0; }}
            QPlainTextEdit {{ border:1px solid {border}; padding:8px; }}
        ''')

    def export_settings(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export preferences', 'z407-preferences.json', 'JSON (*.json)')
        if path:
            try: Path(path).write_text(json.dumps(self.settings.data, indent=2), encoding='utf-8')
            except OSError as exc: self.on_event('error', str(exc))

    def export_diagnostics(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export diagnostics', 'z407-diagnostics.txt', 'Text (*.txt)')
        if path:
            try: Path(path).write_text('Logi Z407 Control Pro 0.1.0\nTransport tested on one local Z407; audible effects not verified.\n' + '\n'.join(self.records), encoding='utf-8')
            except OSError as exc: self.on_event('error', str(exc))

    def make_tray(self, icon):
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip('Logi Z407 Control Pro')
        menu = QMenu()
        menu.addAction('Open controls', self.restore)
        for name in ('VOLUME_UP', 'VOLUME_DOWN', 'BASS_UP', 'BASS_DOWN', 'BLUETOOTH', 'USB', 'AUX'):
            menu.addAction(name.replace('_', ' ').title(), lambda n=name: self.send(Command[n]))
        menu.addAction('Reconnect preferred speaker', lambda: self.worker.submit(self.worker.controller.connect(self.settings.data['preferred'])) if self.settings.data['preferred'] else self.scan())
        menu.addAction('Exit', self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.restore() if reason == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    def restore(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def compact(self):
        from PySide6.QtWidgets import QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle('Z407 mini controls')
        dialog.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label('Relative hardware adjustments · no level readback'))
        for name in ('VOLUME_UP', 'VOLUME_DOWN', 'BASS_UP', 'BASS_DOWN'):
            layout.addWidget(button(name.replace('_', ' ').title(), lambda checked=False, n=name: self.send(Command[n])))
        layout.addWidget(button('Windows mute', lambda: self.audio_action(self.audio.mute)))
        row = QHBoxLayout()
        for name in ('BLUETOOTH', 'USB', 'AUX'):
            row.addWidget(button(name, lambda checked=False, n=name: self.send(Command[n])))
        layout.addLayout(row)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.show()

    def closeEvent(self, event):
        if not self.quitting and self.settings.data['tray'] and self.tray.isSystemTrayAvailable():
            event.ignore()
            self.hide()
        else:
            self.hotkeys.clear()
            self.tray.hide()
            event.accept()

    def quit(self):
        self.quitting = True
        self.close()
        QApplication.instance().quit()

