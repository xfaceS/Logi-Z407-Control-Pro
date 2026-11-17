import pytest
from app.profiles import RelativeState
from app.storage.settings import Settings
from app.ui.hotkeys import parse_shortcut

def test_baseline_and_profiles():
    state = RelativeState()
    with pytest.raises(ValueError): state.preset_delta(2)
    state.establish_baseline()
    state.apply('BASS_UP')
    assert state.preset_delta(3) == 2
    state.apply('VOLUME_DOWN')
    assert state.volume == -1
    with pytest.raises(ValueError): state.preset_delta(99)
    state.invalidate()
    assert not state.calibrated

def test_settings_atomic_persistence(tmp_path):
    path = tmp_path / 'settings.json'
    settings = Settings(path)
    settings.data['theme'] = 'Light'
    settings.save()
    assert Settings(path).data['theme'] == 'Light'
    path.write_text('{invalid')
    assert Settings(path).error

def test_shortcuts():
    assert parse_shortcut('Ctrl+Alt+Up') == (0x4003, 0x26)
    with pytest.raises(ValueError): parse_shortcut('Up')
