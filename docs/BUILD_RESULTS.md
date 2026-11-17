# Actual distribution results — 2026-11-17

Environment: Windows 11 x64 (build 26300), official signature-verified Python
3.13.9, PySide6 6.12.0, Bleak 3.1.0, pycaw 20260927, PyInstaller 6.22.3,
official signature-verified Inno Setup 6.7.4.

- Automated tests: **15 passed** in 2.38 seconds.
- Native source GUI startup/shutdown: **PASS**.
- Native window rendering inspected at 1110×800: **PASS**.
- Read-only real Core Audio enumeration: **PASS**.
- Real Z407 protocol: commands and reconnect tests described in TESTING.md.
- PyInstaller windowed x64 executable generation: **PASS**.
- Dependency license collection: **PASS**.
- Inno Setup installer compilation: **PASS** (unsigned installer generated).
- Final executable PE inspection: **PASS**, x64 architecture 0x8664, GUI subsystem 2.
- No-console source launcher using pythonw: **PASS**, exit 0.
- Earlier diagnostic executable after the ICU packaging correction: **PASS**, exit 0.
- Final windowed executable launch: **BLOCKED BY WINDOWS SMART APP CONTROL**.
  Code Integrity event 3077 reported that the unsigned executable did not meet
  the machine's signing policy. No policy or security setting was changed.
- Final packaged BLE scan: **NOT EXECUTED**, blocked before process startup.
- Final installer install/uninstall acceptance: **NOT EXECUTED**; generated
  installer is also unsigned. Building an installer is distinct from testing it.

The user explicitly chose delivery of unsigned artifacts and a source launcher.
An approved code-signing certificate/service is not available in this environment.
Do not describe this release as signed, hardware-certified, or fully production
validated. Run from source with the signed Python runtime for local use, or arrange
approved code signing for deployment under a policy requiring signed executables.

## Reproducible packaging correction

The initial PyInstaller bundle collected an incompatible `icuuc.dll` from the
builder's PATH. It exports version-suffixed ICU symbols, whereas Qt imports the
Windows system ICU symbols without suffixes. This caused `QtCore` DLL import failure.
`scripts/fix_runtime.py` removes those two build-environment ICU files from the
bundle and retains Qt's matching C++ runtime libraries. Windows 10/11 supplies
the required system ICU. A diagnostic packaged build then launched successfully.

`scripts/build.ps1` normally requires packaged startup to pass before compiling
the installer. `-PackageWithoutLaunch` explicitly packages without that check and
prints a warning; use only when documenting the resulting verification gap.
