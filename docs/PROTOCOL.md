# Compatibility report — 2026-11-17

Reviewed repositories and immutable revisions:

| Reference | Revision |
|---|---|
| freundTech/logi-z407-reverse-engineering | da209d2bfff481ba17b84a1bd0475717343a62a4 |
| androrama/Logitech-Z407-Remote-Control-Web-App---Windows | 273007616d69567fdf2b92ef8cd49773964bc46c |
| androrama/Logitech-Z407-Remote-Control-Web-App---Linux | cbed82688121371f9c9616759ba6b327ba60d1c3 |

The original project is a Bleak proof of concept plus protocol documentation. The
Androrama apps use Quart, Bleak and host multimedia key automation. Windows adds
PyAutoGUI, PyInstaller and Pillow. Linux uses xdotool and includes adapter reset
recovery that this app deliberately does not reproduce. The Windows app marks a
connection ready before handshake confirmation; both maintain an invented initial
volume percentage. This implementation waits for the complete documented handshake
and exposes only relative counts. Real local testing subsequently showed that the
speaker may emit either d40001 or d40003 after 8400 rather than both. Either positive
response now establishes readiness; individual commands still require their ACK.

## Documented protocol and local compatibility findings

Primary reference: https://github.com/freundTech/logi-z407-reverse-engineering/blob/da209d2bfff481ba17b84a1bd0475717343a62a4/doc/Protocol.md

Service `0000fdc2-0000-1000-8000-00805f9b34fb` is advertised when no remote owns
the speaker. Command characteristic `c2e758b9-0e78-41e0-b0cb-98a593193fc5`;
notification characteristic `b84ac9c6-29c5-46d4-bba1-9d534784330f`.
Subscribe first. Send `8405`, await `d40501`; send `8400`, await `d40001` and
`d40003` (the local hardware emits one or the other; both are accepted).
Reference writes use write-without-response; application acknowledgment
notifications are separate from GATT write responses.

| Command | Payload | Acknowledgment |
|---|---|---|
| Bass up/down | 8000 / 8001 | c000 / c001 |
| Volume up/down | 8002 / 8003 | c002 / c003 |
| Bluetooth playback toggle/next/previous | 8004 / 8005 / 8006 | c004 / c005 / c006 |
| Bluetooth/AUX/USB input | 8101 / 8102 / 8103 | c101 / c102 / c103 |

Input status `cf04/cf05/cf06` reports Bluetooth/AUX/USB only when the source changes.
An acknowledgment alone does not prove a current input reading. No documented
absolute bass/volume reads, numeric ranges, EQ bands, firmware capability queries,
or physical dial state notifications exist in these references.

Only one control connection is supported. The physical dial idles out after roughly
five minutes or releases the connection when its batteries are removed. Audio
Bluetooth pairing and the BLE remote handshake are distinct. There is no bypass.

## Local engineering policies and assumptions

Timeouts: 20 s connection, 4 s command/handshake response, 5 s cleanup. Minimum
write spacing 100 ms; maximum eight pending commands. These values are conservative
policies, not verified hardware requirements. Reconnect delays are bounded
exponential backoff, not a substitute for handshake responses. Five attempts maximum.
All uncertain sends stop the connection; no repeat of a potentially applied command.
All state estimates are invalidated on loss. A baseline is a user assertion only.

## Licensing

No LICENSE was present in the three reviewed trees. No reference source or graphics
were copied into the app. Protocol facts and attribution are retained separately.
