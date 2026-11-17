class RelativeState:
    """Counts acknowledged session adjustments, never a measured hardware level."""
    def __init__(self):
        self.invalidate()

    def invalidate(self):
        self.volume = 0
        self.bass = 0
        self.calibrated = False

    def establish_baseline(self):
        self.bass = 0
        self.calibrated = True

    def apply(self, name):
        if name == 'VOLUME_UP': self.volume += 1
        elif name == 'VOLUME_DOWN': self.volume -= 1
        elif name == 'BASS_UP': self.bass += 1
        elif name == 'BASS_DOWN': self.bass -= 1

    def preset_delta(self, target):
        if not self.calibrated:
            raise ValueError('Establish a manual bass baseline first.')
        if type(target) is not int or not -6 <= target <= 6:
            raise ValueError('Preset must be within six steps of your baseline.')
        delta = target - self.bass
        if abs(delta) > 6:
            raise ValueError('More than six steps required. Adjust manually and re-establish your baseline.')
        return delta
