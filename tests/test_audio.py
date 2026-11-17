from types import SimpleNamespace
from app.audio.windows import WindowsAudio

def test_core_audio_volume_and_mute_dispatch():
    calls = []
    endpoint = SimpleNamespace(SetMasterVolumeLevelScalar=lambda v, context: calls.append(('volume', v)),
                               GetMute=lambda: False, SetMute=lambda v, context: calls.append(('mute', v)))
    audio = object.__new__(WindowsAudio)
    audio.api = SimpleNamespace(GetSpeakers=lambda: SimpleNamespace(EndpointVolume=endpoint))
    audio.volume(120)
    audio.volume(-2)
    audio.mute()
    assert calls == [('volume', 1), ('volume', 0), ('mute', True)]
