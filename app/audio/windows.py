"""Windows Core Audio endpoint/session control; no BLE fallback."""
import ctypes

class WindowsAudio:
    def __init__(self):
        from pycaw.pycaw import AudioUtilities
        self.api = AudioUtilities

    def snapshot(self):
        from pycaw.constants import EDataFlow, DEVICE_STATE
        default = self.api.GetSpeakers()
        devices = self.api.GetAllDevices(data_flow=EDataFlow.eRender.value, device_state=DEVICE_STATE.ACTIVE.value)
        sessions = self.api.GetAllSessions()
        return default, devices, sessions

    def volume(self, percent):
        self.api.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(max(0, min(100, percent)) / 100, None)

    def mute(self):
        endpoint = self.api.GetSpeakers().EndpointVolume
        endpoint.SetMute(not endpoint.GetMute(), None)

    @staticmethod
    def media(action):
        # Standard Windows multimedia virtual keys, explicitly PC controls.
        key = {'play': 0xB3, 'next': 0xB0, 'previous': 0xB1}[action]
        ctypes.windll.user32.keybd_event(key, 0, 0, 0)
        ctypes.windll.user32.keybd_event(key, 0, 2, 0)
