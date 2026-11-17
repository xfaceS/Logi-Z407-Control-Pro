# Attribution and licenses

Protocol research: freundTech, https://github.com/freundTech/logi-z407-reverse-engineering
Windows and Linux reference applications: Androrama,
https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Windows and
https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Linux.

No explicit LICENSE file was present in any reference checkout on 2026-11-17.
Their application source, artwork and documentation are not redistributed in the
installer. This application is independently implemented using documented protocol
facts. Local research checkouts are excluded from packaging. Do not assume those
repositories grant permission to reuse their code.

Runtime dependencies: Python (PSF license), PySide6/Qt (LGPLv3/commercial;
dynamically linked DLLs retained in the distribution), Bleak (MIT), pycaw (MIT),
comtypes (MIT), psutil (BSD), WinRT Python packages (MIT).
Dependency license texts are collected in dist/LogiZ407ControlPro/licenses during
release preparation. Source and modifications for this application are supplied
alongside the distribution. Qt source is available at https://download.qt.io/.
Users may replace the dynamically linked Qt libraries for compatible builds.

Not affiliated with or endorsed by Logitech. Logitech and Z407 are trademarks of
their respective owners. The application icon is original geometric artwork.
