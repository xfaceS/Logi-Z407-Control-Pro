# Troubleshooting

- **No device found:** ensure speaker power, range, and Windows Bluetooth. Remove
  physical dial batteries or let it idle five minutes; stop other Z407 controllers.
- **Adapter unavailable / scan error:** check Windows Bluetooth Settings and Device
  Manager. The scan error includes the WinRT message. The app never resets adapters.
- **Connection or handshake timeout:** speaker may already have a remote owner.
  Release that controller manually and reconnect. A successful audio pairing does
  not mean the BLE control channel is free.
- **Missing characteristic:** do not send commands to that device. Check that the
  discovered service belongs to a Z407. Other hardware/firmware is unsupported.
- **Command timeout:** the speaker may have applied it without returning an ACK.
  Reconnect and listen before further adjustments. Never compensate by blindly
  repeating bass increases.
- **Profile mismatch:** physical dial movement and reaching a limit are not readable.
  Invalidate the baseline and establish a new reference by listening.
- **Media buttons do nothing:** the target player must support Windows multimedia
  keys. Speaker playback commands apply to Bluetooth audio, not the PC session.
- **Shortcut unavailable:** change or disable conflicting combinations in Settings.
- **Window disappeared:** restore using the system tray. Tray Exit releases BLE.

Diagnostics exports recent events with MAC addresses redacted. Review exports before
sharing: OS error strings may contain other local identifiers. Settings are stored
under `%LOCALAPPDATA%\LogiZ407ControlPro`. Uninstall preserves those preferences.
