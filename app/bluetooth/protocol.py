"""Protocol facts from freundTech's Protocol.md; no absolute level API exists."""
from enum import Enum

SERVICE = '0000fdc2-0000-1000-8000-00805f9b34fb'
COMMAND = 'c2e758b9-0e78-41e0-b0cb-98a593193fc5'
RESPONSE = 'b84ac9c6-29c5-46d4-bba1-9d534784330f'

class Command(Enum):
    BASS_UP = b'\x80\x00'
    BASS_DOWN = b'\x80\x01'
    VOLUME_UP = b'\x80\x02'
    VOLUME_DOWN = b'\x80\x03'
    PLAY_PAUSE = b'\x80\x04'
    NEXT = b'\x80\x05'
    PREVIOUS = b'\x80\x06'
    BLUETOOTH = b'\x81\x01'
    AUX = b'\x81\x02'
    USB = b'\x81\x03'

    @property
    def acknowledgment(self):
        return bytes((self.value[0] + 0x40, self.value[1]))

INPUT_STATUS = {b'\xcf\x04': 'Bluetooth', b'\xcf\x05': 'AUX', b'\xcf\x06': 'USB'}
