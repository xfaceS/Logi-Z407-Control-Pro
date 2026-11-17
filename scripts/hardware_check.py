"""Explicit real-device acceptance checks; never runs as part of pytest."""
import argparse
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.bluetooth.controller import Controller
from app.bluetooth.protocol import Command

async def run(inputs=False):
    controller = Controller(lambda kind, value: print(kind, 'identifiers redacted' if kind == 'devices' else value))
    devices = await controller.scan()
    if len(devices) != 1:
        raise RuntimeError('Expected exactly one candidate. Use the GUI to choose explicitly.')
    try:
        await controller.connect(devices[0])
        for command in (Command.VOLUME_DOWN, Command.VOLUME_UP, Command.BASS_DOWN, Command.BASS_UP):
            await controller.send(command)
        if inputs:
            for command in (Command.BLUETOOTH, Command.AUX, Command.USB):
                await controller.send(command)
                await asyncio.sleep(.5)
        await controller.disconnect()
        await controller.connect(devices[0])
        print('Transport acceptance passed. Audible effects and power-loss recovery require manual verification.')
    finally:
        await controller.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-inputs', action='store_true', help='Switch Bluetooth → AUX → USB; leaves USB selected')
    args = parser.parse_args()
    asyncio.run(run(args.include_inputs))
