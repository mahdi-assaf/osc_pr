import logging
from socket import socket, AF_INET, SOCK_STREAM
from osi.interface.omi.params import Tcc2InterfaceParams, AmplifierInterfaceParams, \
    ChassisInterfaceParams, WxcInterfaceParams
from osi.interface.omi.omi_interfaces import AmplifierOmiInterface, WxcOmiInterface
from telnetlib import Telnet


class EquipmentInterface:
    """ Abstract class of equipment interfaces.

        Args:
            params: it must be an object whose the parameters are described in `drivers.cisco.params`.
                One params object for each interface object.

        Attributes:
            _params: store `params`
            _socket: (socket.socket) store the `socket`

        Properties:
            params: returns the parameters of the interface
            socket: returns the TCP/IP socket

        Methods:
            login;
            close.
    """

    def __init__(self, params):
        self._params = params
        self._socket = None
        # self.socket.setblocking(True)

    @property
    def params(self):
        return self._params

    @property
    def socket(self):
        return self._socket

    # TCP/IP Connection and login
    def _tcpip_connect(self):
        host = self.params.ip_address
        port = self.params.port
        self._socket = socky = socket(AF_INET, SOCK_STREAM)
        print(f"Connecting to {host}:{port}")
        socky.connect((host, port))
        logging.debug(f"Connected recv: {str(socky.recv(1024))}")

    def _tcpip_close(self):
        self.socket.close()

    def login(self):
        """ It creates a tcpip connection (whose the handler is stored in `self.socket`) and logs in by using
        `self.params.username` and `self.params.password`.
        """
        username = self.params.username
        password = self.params.password

        self._tcpip_connect()
        socky = self.socket
        socky.sendall(username + b'\r')
        socky.sendall(password + b'\r')
        logging.debug('\n' + str(socky.recv(1024)))

    def close(self):
        """ It closes all the connections.
        """
        self._tcpip_close()


class Tcc2Interface(EquipmentInterface):
    """ Interface to the CISCO Advanced Timing Communications and Control (TCC2) card.
        More details in https://www.cisco.com/c/en/us/td/docs/optical/spares/15454/sonet_sdh/guides/TCC2SP.html

        Args:
            params: (Tcc2InterfaceParams) the object containing all the parameters

        Attributes:
            _params: store `params`
            _socket: (socket.socket) store the `socket`

        Properties:
            params: returns the parameters of the interface
            socket: returns the TCP/IP socket

        Methods:
            login;
            close.
    """

    def __init__(self, params: Tcc2InterfaceParams):
        super().__init__(params)

    def _telnet_login(self):
        ip = self.params.ip_address
        username = self.params.username
        password = self.params.password

        telnet = Telnet(ip)
        telnet.read_until(b"Login: ")
        telnet.write(username + b"\r")
        telnet.read_until(b"Password:")
        telnet.write(password + b"\r")
        return telnet

    def _set_telnet_relay(self, value=None):
        if not value:
            value = b'1'
        telnet = self._telnet_login()

        telnet.read_until(b'->')
        telnet.write(b'setTelnetRelay ' + value + b"\n")
        telnet.read_until(b'->')
        telnet.write(b'logout' + b"\n")
        telnet.close()

    def login(self):
        """ It first enables the debug mode of the chassis by setting setTelnetRelay to 1 through telnet.
        Then, it logs in via TCP/IP. For more details see `login` method of `Tcc2InterfaceParams` object.
        """
        self._set_telnet_relay(b'1')
        super().login()


class AmplifierInterface(EquipmentInterface):
    """ Interface to the CISCO EDFA card.

        Args:
            params (Tcc2InterfaceParams): the object containing all the parameters

        Attributes:
            _params: store `params`
            _socket: (socket.socket) store the `socket`
            _interface (AmplifierOmiInterface or AmplifierTl1Interface): the low level interface to the amplifier. The
            type depends on `self.params.protocol`

        Properties:
            params: returns the parameters of the interface
            socket: returns the TCP/IP socket

        Methods:
            login()
            close()

    """

    def __init__(self, params: AmplifierInterfaceParams):
        super().__init__(params)
        self._interface = None

    def __repr__(self):
        return f'{type(self).__name__}(params={repr(self.params)})'

    def __str__(self):
        current1, current2 = self.get_current()
        return '\n'.join([f'{type(self).__name__} {self.params.uid}',
                          f'  Mode:                 {self.get_mode()}',
                          f'  Current of 1st stage: {current1} mA',
                          f'  Current of 2nd stage: {current2} mA',
                          f'  Effective gain:       {self.get_gain():.1f} dB',
                          f'  Tilt:                 {self.get_tilt():.1f} dB',
                          f'  VOA attenuation:      {self.get_voa():.1f} dB',
                          f'  Input power:          {self.get_input_power():.1f} dBm',
                          f'  Output power:         {self.get_output_power():.1f} dBm',
                          f'  Signal output power:  {self.get_tot_signal_out_power():.1f} dBm'])

    @property
    def interface(self):
        return self._interface

    def login(self):
        super().login()
        sockey = self.socket
        if self.params.protocol.lower() == 'omi':
            self._interface = AmplifierOmiInterface(sockey)

    def get_mode(self):
        """ It returns the operating mode. It can be "constant current", "constant power" and "constant gain".

        :return: mode: (string) the operating mode of the amplifier.
        """
        mode = self.interface.get_mode()
        return mode

    def get_current(self):
        """ It returns the current value of the pumps of the two stages.

        :return: tuple (current1, current2)
            current1: (float) the current value of the first amplification stage (mA)
            current2: (float) the current value of the second amplification stage (mA)
        """
        current1, current2 = self.interface.get_current()
        return current1, current2

    def get_gain(self):
        gain = self.interface.get_gain()
        return gain

    def get_tilt(self):
        """Amplifier tilt in frequency (dB)"""
        tilt = -self.interface.get_tilt()
        return tilt

    def get_input_power(self):
        input_power = self.interface.get_input_power()
        return input_power

    def get_output_power(self, il=None):
        output_power = self.interface.get_output_power()
        return (output_power - il) if il else output_power

    def get_tot_signal_out_power(self, il=None):
        tot_signal_out_power = self.interface.get_tot_signal_out_power()
        return (tot_signal_out_power - il) if il else tot_signal_out_power

    def get_noise_figure(self):
        noise_figure = self.interface.get_noise_figure()
        return noise_figure

    def get_voa(self):
        voa = self.interface.get_voa()
        return voa

    def set_mode(self, mode):
        """ Set amplifier's mode. It can be "constant_current", "constant_power" and "constant_gain".
        :param mode: (str) it identifies the operating mode. Can be "constant_current", "constant_power" and
        "constant_gain"
        """
        if (mode.lower() != "constant_current") and (mode.lower() != "constant_power") and (
                mode.lower() != "constant_gain"):
            logging.error(f'{mode} is not a valid operating mode.')
        self.interface.set_mode(mode)

    def set_gain(self, gain):
        """ Set amplifier's gain (dB). Only first decimal digit is considered.
                :param gain: (float) amplifier's gain (dB)
        """
        self.interface.set_gain(gain)

    def set_current(self, current1, current2):
        """ Set amplifier's currents (mA). Only first decimal digit is considered.
                :param current1: (float) current of the 1st stage (mA)
                :param current2: (float) current of the 2nd stage (mA)
        """
        self.interface.set_current(current1, current2)

    def set_tilt(self, tilt):
        """ Set amplifier's tilt (dB). Only first decimal digit is considered.
                :param tilt: (float) amplifier's tilt in frequency (dB)
        """
        self.interface.set_tilt(-tilt)

    def set_output_power(self, power, il=None):
        power = (power + il) if il else power
        self.interface.set_output_power(power)

    def set_voa(self, attenuation):
        self.interface.set_voa(attenuation)

    # TODO: TBI
    # def set_apr(self, apr):
    #     self.interface.set_apr(apr)

    def configure_operational(self, operational: dict):
        if 'pout_target' in operational and 'gain_target' in operational:
            logging.exception(f'Amplifier `operational` dictionary in {self.params.uid} '
                              f'has both `pout_target` and `gain_target`')
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


class ChassisInterface:
    """
    """

    def __init__(self, params: ChassisInterfaceParams):
        self._params = params
        self._tcc2interface = Tcc2Interface(Tcc2InterfaceParams(self.params.ip_address, 23, self.params.username,
                                                                self.params.password))
        # TODO: is it better to configure it at the beginning?
        self.amplifiers = {}

    def __str__(self):
        return '\n'.join([f'{type(self).__name__}',
                          f'  Parameters: \n  {self.params}'])

    @property
    def params(self):
        return self._params

    @property
    def tcc2interface(self):
        return self._tcc2interface

    def login(self):
        self.tcc2interface.login()

    def close(self):
        self.tcc2interface.close()

    def add_amplifier(self, amplifier_params: AmplifierInterfaceParams):
        uid = amplifier_params.uid
        self.amplifiers[uid] = AmplifierInterface(amplifier_params)
        return


class WxcInterface(EquipmentInterface):
    def __init__(self, params: WxcInterfaceParams):
        super().__init__(params)
        self._interface = None

    def _telnet_login(self):
        ip = self.params.ip_address
        username = self.params.username
        password = self.params.password

        telnet = Telnet(ip)
        telnet.read_until(b"Login: ")
        telnet.write(username + b"\r")
        telnet.read_until(b"Password:")
        telnet.write(password + b"\r")
        return telnet

    def _set_telnet_relay(self, value=None):
        if not value:
            value = b'1'
        telnet = self._telnet_login()

        telnet.read_until(b'->')
        telnet.write(b'setTelnetRelay ' + value + b"\n")
        telnet.read_until(b'->')
        telnet.write(b'logout' + b"\n")
        telnet.close()

    @property
    def interface(self):
        return self._interface

    def login(self):
        super().login()
        sockey = self.socket
        self._interface = WxcOmiInterface(sockey)

    def set_port_state(self):
        self.interface.set_port_state()

    def init_channel_WXC(self):
        self.interface.init_channel_WXC(WXC=None, channel=1, freq=191.325, bw=50, att=1, mux_dmx="MUX")


import logging
from socket import socket, AF_INET, SOCK_STREAM
from osi.interface.omi.params import Tcc2InterfaceParams, AmplifierInterfaceParams, \
    ChassisInterfaceParams, WxcInterfaceParams
from osi.interface.omi.omi_interfaces import AmplifierOmiInterface, WxcOmiInterface
from telnetlib import Telnet


class EquipmentInterface:
    """ Abstract class of equipment interfaces.

        Args:
            params: it must be an object whose the parameters are described in `drivers.cisco.params`.
                One params object for each interface object.

        Attributes:
            _params: store `params`
            _socket: (socket.socket) store the `socket`

        Properties:
            params: returns the parameters of the interface
            socket: returns the TCP/IP socket

        Methods:
            login;
            close.
    """

    def __init__(self, params):
        self._params = params
        self._socket = None
        # self.socket.setblocking(True)

    @property
    def params(self):
        return self._params

    @property
    def socket(self):
        return self._socket

    # TCP/IP Connection and login
    def _tcpip_connect(self):
        host = self.params.ip_address
        port = self.params.port
        self._socket = socky = socket(AF_INET, SOCK_STREAM)
        print(f"Connecting to {host}:{port}")
        socky.connect((host, port))
        logging.debug(f"Connected recv: {str(socky.recv(1024))}")

    def _tcpip_close(self):
        self.socket.close()

    def login(self):
        """ It creates a tcpip connection (whose the handler is stored in `self.socket`) and logs in by using
        `self.params.username` and `self.params.password`.
        """
        username = self.params.username
        password = self.params.password

        self._tcpip_connect()
        socky = self.socket
        socky.sendall(username + b'\r')
        socky.sendall(password + b'\r')
        logging.debug('\n' + str(socky.recv(1024)))

    def close(self):
        """ It closes all the connections.
        """
        self._tcpip_close()


class Tcc2Interface(EquipmentInterface):
    """ Interface to the CISCO Advanced Timing Communications and Control (TCC2) card.
        More details in https://www.cisco.com/c/en/us/td/docs/optical/spares/15454/sonet_sdh/guides/TCC2SP.html

        Args:
            params: (Tcc2InterfaceParams) the object containing all the parameters

        Attributes:
            _params: store `params`
            _socket: (socket.socket) store the `socket`

        Properties:
            params: returns the parameters of the interface
            socket: returns the TCP/IP socket

        Methods:
            login;
            close.
    """

    def __init__(self, params: Tcc2InterfaceParams):
        super().__init__(params)

    def _telnet_login(self):
        ip = self.params.ip_address
        username = self.params.username
        password = self.params.password

        telnet = Telnet(ip)
        telnet.read_until(b"Login: ")
        telnet.write(username + b"\r")
        telnet.read_until(b"Password:")
        telnet.write(password + b"\r")
        return telnet

    def _set_telnet_relay(self, value=None):
        if not value:
            value = b'1'
        telnet = self._telnet_login()

        telnet.read_until(b'->')
        telnet.write(b'setTelnetRelay ' + value + b"\n")
        telnet.read_until(b'->')
        telnet.write(b'logout' + b"\n")
        telnet.close()

    def login(self):
        """ It first enables the debug mode of the chassis by setting setTelnetRelay to 1 through telnet.
        Then, it logs in via TCP/IP. For more details see `login` method of `Tcc2InterfaceParams` object.
        """
        self._set_telnet_relay(b'1')
        super().login()


class AmplifierInterface(EquipmentInterface):
    """ Interface to the CISCO EDFA card.

        Args:
            params (Tcc2InterfaceParams): the object containing all the parameters

        Attributes:
            _params: store `params`
            _socket: (socket.socket) store the `socket`
            _interface (AmplifierOmiInterface or AmplifierTl1Interface): the low level interface to the amplifier. The
            type depends on `self.params.protocol`

        Properties:
            params: returns the parameters of the interface
            socket: returns the TCP/IP socket

        Methods:
            login()
            close()

    """

    def __init__(self, params: AmplifierInterfaceParams):
        super().__init__(params)
        self._interface = None

    def __repr__(self):
        return f'{type(self).__name__}(params={repr(self.params)})'

    def __str__(self):
        current1, current2 = self.get_current()
        return '\n'.join([f'{type(self).__name__} {self.params.uid}',
                          f'  Mode:                 {self.get_mode()}',
                          f'  Current of 1st stage: {current1} mA',
                          f'  Current of 2nd stage: {current2} mA',
                          f'  Effective gain:       {self.get_gain():.1f} dB',
                          f'  Tilt:                 {self.get_tilt():.1f} dB',
                          f'  VOA attenuation:      {self.get_voa():.1f} dB',
                          f'  Input power:          {self.get_input_power():.1f} dBm',
                          f'  Output power:         {self.get_output_power():.1f} dBm',
                          f'  Signal output power:  {self.get_tot_signal_out_power():.1f} dBm'])

    @property
    def interface(self):
        return self._interface

    def login(self):
        super().login()
        sockey = self.socket
        if self.params.protocol.lower() == 'omi':
            self._interface = AmplifierOmiInterface(sockey)

    def get_mode(self):
        """ It returns the operating mode. It can be "constant current", "constant power" and "constant gain".

        :return: mode: (string) the operating mode of the amplifier.
        """
        mode = self.interface.get_mode()
        return mode

    def get_current(self):
        """ It returns the current value of the pumps of the two stages.

        :return: tuple (current1, current2)
            current1: (float) the current value of the first amplification stage (mA)
            current2: (float) the current value of the second amplification stage (mA)
        """
        current1, current2 = self.interface.get_current()
        return current1, current2

    def get_gain(self):
        gain = self.interface.get_gain()
        return gain

    def get_tilt(self):
        """Amplifier tilt in frequency (dB)"""
        tilt = -self.interface.get_tilt()
        return tilt

    def get_input_power(self):
        input_power = self.interface.get_input_power()
        return input_power

    def get_output_power(self, il=None):
        output_power = self.interface.get_output_power()
        return (output_power - il) if il else output_power

    def get_tot_signal_out_power(self, il=None):
        tot_signal_out_power = self.interface.get_tot_signal_out_power()
        return (tot_signal_out_power - il) if il else tot_signal_out_power

    def get_noise_figure(self):
        noise_figure = self.interface.get_noise_figure()
        return noise_figure

    def get_voa(self):
        voa = self.interface.get_voa()
        return voa

    def set_mode(self, mode):
        """ Set amplifier's mode. It can be "constant_current", "constant_power" and "constant_gain".
        :param mode: (str) it identifies the operating mode. Can be "constant_current", "constant_power" and
        "constant_gain"
        """
        if (mode.lower() != "constant_current") and (mode.lower() != "constant_power") and (
                mode.lower() != "constant_gain"):
            logging.error(f'{mode} is not a valid operating mode.')
        self.interface.set_mode(mode)

    def set_gain(self, gain):
        """ Set amplifier's gain (dB). Only first decimal digit is considered.
                :param gain: (float) amplifier's gain (dB)
        """
        self.interface.set_gain(gain)

    def set_current(self, current1, current2):
        """ Set amplifier's currents (mA). Only first decimal digit is considered.
                :param current1: (float) current of the 1st stage (mA)
                :param current2: (float) current of the 2nd stage (mA)
        """
        self.interface.set_current(current1, current2)

    def set_tilt(self, tilt):
        """ Set amplifier's tilt (dB). Only first decimal digit is considered.
                :param tilt: (float) amplifier's tilt in frequency (dB)
        """
        self.interface.set_tilt(-tilt)

    def set_output_power(self, power, il=None):
        power = (power + il) if il else power
        self.interface.set_output_power(power)

    def set_voa(self, attenuation):
        self.interface.set_voa(attenuation)

    # TODO: TBI
    # def set_apr(self, apr):
    #     self.interface.set_apr(apr)

    def configure_operational(self, operational: dict):
        if 'pout_target' in operational and 'gain_target' in operational:
            logging.exception(f'Amplifier `operational` dictionary in {self.params.uid} '
                              f'has both `pout_target` and `gain_target`')
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


class ChassisInterface:
    """
    """

    def __init__(self, params: ChassisInterfaceParams):
        self._params = params
        self._tcc2interface = Tcc2Interface(Tcc2InterfaceParams(self.params.ip_address, 23, self.params.username,
                                                                self.params.password))
        # TODO: is it better to configure it at the beginning?
        self.amplifiers = {}

    def __str__(self):
        return '\n'.join([f'{type(self).__name__}',
                          f'  Parameters: \n  {self.params}'])

    @property
    def params(self):
        return self._params

    @property
    def tcc2interface(self):
        return self._tcc2interface

    def login(self):
        self.tcc2interface.login()

    def close(self):
        self.tcc2interface.close()

    def add_amplifier(self, amplifier_params: AmplifierInterfaceParams):
        uid = amplifier_params.uid
        self.amplifiers[uid] = AmplifierInterface(amplifier_params)
        return


class WxcInterface(EquipmentInterface):
    def __init__(self, params: WxcInterfaceParams):
        super().__init__(params)
        self._interface = None

    def _telnet_login(self):
        ip = self.params.ip_address
        username = self.params.username
        password = self.params.password

        telnet = Telnet(ip)
        telnet.read_until(b"Login: ")
        telnet.write(username + b"\r")
        telnet.read_until(b"Password:")
        telnet.write(password + b"\r")
        return telnet

    def _set_telnet_relay(self, value=None):
        if not value:
            value = b'1'
        telnet = self._telnet_login()

        telnet.read_until(b'->')
        telnet.write(b'setTelnetRelay ' + value + b"\n")
        telnet.read_until(b'->')
        telnet.write(b'logout' + b"\n")
        telnet.close()

    @property
    def interface(self):
        return self._interface

    def login(self):
        super().login()
        sockey = self.socket
        self._interface = WxcOmiInterface(sockey)

    def set_port_state(self):
        self.interface.set_port_state()

    def init_channel_WXC(self):
        self.interface.init_channel_WXC(WXC=None, channel=1, freq=191.325, bw=50, att=1, mux_dmx="MUX")


