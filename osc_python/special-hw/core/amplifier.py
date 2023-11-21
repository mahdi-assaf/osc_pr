from core.device import Device


class Amplifier(Device):
    def __init__(self, uid: str, device_info: dict, credentials: dict):
        super().__init__(uid, device_info)

        self._driver = self._driver_class(**credentials)

    @property
    def driver(self):
        return self._driver

    @property
    def constants(self):
        return self._driver.constants

    def get(self, *args):
        return self._driver.get(*args)

    def get_config(self):
        return

    def set(self, **kwargs):
        return self._driver.set(**kwargs)

    def configure_operational(self, operational: dict):
        if 'pout_target' in operational and 'gain_target' in operational:
            pass
        elif 'pout_target' in operational:
            mode = 'constant_power'
            pout_target = operational['pout_target']
            tilt_target = operational['tilt_target']
            self.set_mode(mode)
            self.set_output_power(pout_target)
            self.set_tilt(tilt_target)
        elif 'gain_target' in operational:
            mode = 'constant_gain'
            gain_target = operational['gain_target']
            tilt_target = operational['tilt_target']
            self.set_mode(mode)
            self.set_gain(gain_target)
            self.set_tilt(tilt_target)
