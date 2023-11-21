from core.definitions import DRIVER_DICT


def access_driver(**kwargs):
    try:
        device_type = kwargs.get("device")
        _ = DRIVER_DICT[device_type]
    except KeyError as e:
        raise e

    device_dict = DRIVER_DICT
    for value in kwargs.values():
        device_dict = device_dict[value]
    return device_dict


class Device:
    def __init__(self, uid: str, device_info: dict):
        self._uid = uid
        self._device = device_info.get("device")
        self._device_type = device_info.get("type")
        self._variety = device_info.get("variety")
        self._driver_class = access_driver(
            device=self._device,
            type=self._device_type,
            variety=self._variety
        )

    @property
    def uid(self):
        return self._uid

    @property
    def device(self):
        return self._device

    @property
    def device_type(self):
        return self._device_type

    @property
    def variety(self):
        return self._variety

    def get(self, *args):
        pass

    def get_config(self, *args):
        pass

    def set(self, **kwargs):
        pass

    def connect(self):
        pass

    def close(self):
        pass
