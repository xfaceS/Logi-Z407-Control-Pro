# Test results — 2026-11-17

## Automated simulated tests

Run `.python/python.exe -m pytest -q` or use a supported Python environment.
The suite covers exact command payloads/ACKs; handshake failure; both locally
observed handshake variants; all control commands; queue serialization/limits;
stale command rejection; uncertain-send no-retry; input notifications; reconnect;
settings recovery/persistence; profile bounds/baselines; shortcut parsing;
native Qt window/tray construction and shutdown; Windows audio API dispatch.
FakeClient exists only under tests and is never selected in production.
Final automated run: **15 passed** on Windows 11, Python 3.13.9.

## Real local Z407 transport tests

The test environment has a Z407 advertising the expected service. Identifiers are
redacted. No adapter resets, pairing removals or factory resets were performed.

| Check | Result |
|---|---|
| Real BLE discovery | PASS: one matching service advertiser |
| Required GATT service/characteristics | PASS |
| Initial handshake | PASS after compatibility correction |
| Volume down/up | PASS: c003 / c002 received |
| Bass down/up | PASS: c001 / c000 received |
| Bluetooth request | PASS: c101 received; current source not independently reported |
| AUX request | PASS: c102, then cf05 source-change report |
| USB request | PASS: c103, then cf06 source-change report |
| Three manual disconnect/reconnect cycles | PASS: fresh handshake and c103 each cycle |
| Audible bass/volume effect | NOT EXECUTED: requires listener confirmation |
| Power interruption recovery | NOT EXECUTED: simulated connection loss tested only |
| Physical dial contention/saturation | NOT EXECUTED |
| Long-duration repeated-interaction soak | NOT EXECUTED |

Hardware was left with USB requested. Each volume/bass test sent one down then one
up; endpoint saturation means an exact restoration cannot be guaranteed.

Important observed difference from the written protocol: after 8400 the local
speaker emitted d40001 alone on initial connections, and d40003 alone on subsequent
connections. Requiring both incorrectly caused timeouts. The implementation now
accepts either documented positive response and still requires individual command
ACKs. Unknown notification cf0b was observed and is not interpreted.

Windows Core Audio: real read-only enumeration succeeded for the default playback
endpoint, five active outputs, two sessions, and the master scalar volume. Write
dispatch is automatically tested against a fake endpoint; actual Windows volume
changes, media key delivery to players, and global shortcut conflicts still need
interactive user verification.

## Reproduce hardware checks explicitly

`python scripts/hardware_check.py` sends one down/up volume and bass sequence and
reconnects. `--include-inputs` additionally switches Bluetooth → AUX → USB.
`python scripts/reconnect_check.py` performs three reconnect cycles requesting USB.
These scripts never run in pytest. Confirm listening tests manually; an ACK proves
protocol reception, not a measured acoustic change.

## Distribution checks

The release build runs unit tests, builds PyInstaller's windowed x64 directory,
collects licenses and smoke-tests the packaged executable before Inno Setup.
See BUILD_RESULTS.md for actual final build and installer validation results.
Remote authentication tests are not applicable: no remote service ships in 0.1.0.
Software EQ is disabled. No production or complete hardware certification is claimed.
