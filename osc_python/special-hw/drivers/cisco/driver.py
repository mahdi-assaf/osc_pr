import time

from drivers.cisco.omi_interfaces import AmplifierOmiInterface
from drivers.cisco.params import AmplifierInterfaceParams
from drivers.cisco.user import AmplifierInterface
from core.constants import *
from socket import socket, MSG_DONTWAIT, MSG_PEEK
from drivers.cisco.utils import get_string_between
import logging
from numpy import int32
from telnetlib import Telnet



class CiscoEDFA17:
    def __init__(self, **kwargs):
        # todo la connessione viene instanziata nel costruttore
        amp_params = AmplifierInterfaceParams(
            ip_address=kwargs.get("ip_address"),
            port=kwargs.get("port"),
            username=kwargs.get("username"),
            password=kwargs.get("password"),
            protocol=kwargs.get("protocol")

        )
        amp_int = AmplifierInterface(amp_params)
        amp_int.login()
        self._omi_interface = AmplifierOmiInterface(amp_int.socket)



    def get(self, *args):
        data = {}
        for arg in args:
            if arg == STATE_GAIN:
                data[arg] = self._omi_interface.get_gain()
            if arg == STATE_TILT:
                self._omi_interface.get_tilt()
            if arg == STATE_INPUT_POWER:
                self._omi_interface.get_input_power()
            if arg == STATE_OUTPUT_POWER:
                self._omi_interface.get_output_power()
            if arg == STATE_SERVICE:
                # todo
                pass
        return data

    def set(self, **kwargs):
        for k, v in kwargs:
            if k == CONFIG_GAIN:
                self._omi_interface.set_gain(v)
            if k == CONFIG_TILT:
                self._omi_interface.set_tilt(v)
            if k == CONFIG_OUTPUT_ENABLED:
                print("not supported")
                pass
            if k == CONFIG_RANGE:
                pass
            if k == CONFIG_MODE:
                self._omi_interface.set_mode(v)
            if k == CONFIG_POWER:
                self._omi_interface.set_output_power(v)


class CiscoEDFA35(AmplifierOmiInterface):
    """ Interface to the CISCO EDFA card.

        Args:
            socky: (socket.socket) object containing the TCP/IP socket

        Attributes:
            _socket: (socket.socket) store the `socket`

        Properties:
            socket: returns the TCP/IP socket

        Methods:
            .
    """

    def __init__(self, **kwargs):
        # todo la connessione viene instanziata nel costruttore
        amp_params = AmplifierInterfaceParams(
            ip_address=kwargs.get("ip_address"),
            port=kwargs.get("port"),
            username=kwargs.get("username"),
            password=kwargs.get("password"),
            protocol=kwargs.get("protocol"),

        )
        self._amp_int = AmplifierInterface(amp_params)
        self._amp_int.login()
        super().__init__(self._amp_int.socket)
        self._direction = kwargs.get("direction")

    # def __del__(self):
    #     print("del")
    #     self.socket.close()

    def close(self):
        self.socket.close()

    def connect(self):
        self._amp_int.login()
        self._socket = self._amp_int.socket



    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        self._direction = direction


    def is_socket_closed(self) -> bool:
        sock = self._socket
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = sock.recv(16, MSG_DONTWAIT | MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            print("unexpected exception when checking if a socket is closed")
            return False
        return False

    def get(self, *args):
        data = {}
        for arg in args:
            if arg == STATE_GAIN:
                data[arg] = self.get_gain()
            if arg == STATE_TILT:
                self.get_tilt()
            if arg == STATE_INPUT_POWER:
                self.get_input_power()
            if arg == STATE_OUTPUT_POWER:
                self.get_output_power()
            if arg == STATE_SERVICE:
                # todo
                pass
        return data

    def set(self, **kwargs):
        for k, v in kwargs:
            if k == CONFIG_GAIN:
                self.set_gain(v)
            if k == CONFIG_TILT:
                self.set_tilt(v)
            if k == CONFIG_OUTPUT_ENABLED:
                print("not supported")
                pass
            if k == CONFIG_RANGE:
                pass
            if k == CONFIG_MODE:
                self.set_mode(v)
            if k == CONFIG_POWER:
                self.set_output_power(v)

    def get_mode(self):
        start_string = 'omi_read(21, 1, 1, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[21, 1, 1, 1, 0])
        mode_value = int(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        if mode_value == 0:
            mode = "constant_current"
        elif mode_value == 1:
            mode = "constant_power"
        elif mode_value == 2:
            mode = "constant_gain"
        else:
            logging.exception(f'Unrecognized mode code {mode_value}.')
            mode = 'null'
        return mode

    def get_current(self):
        start_string_current1 = 'omi_read(24, 1, 0)\\n\\rI32-Value is:'
        start_string_current2 = 'omi_read(24, 2, 0)\\n\\rI32-Value is:'
        end_string = '\\n\\rCompleted'
        current1_bin = self._omi_read(4096, *[24, 1, 0])
        current1 = float(get_string_between(str(current1_bin), start_string_current1,
                                            end_string)) / 10  # The value is divided by 10 to take into account the first decimal digit
        current2_bin = self._omi_read(4096, *[24, 2, 0])
        current2 = float(get_string_between(str(current2_bin), start_string_current2,
                                            end_string)) / 10  # The value is divided by 10 to take into account the first decimal digit
        return current1, current2

    def get_gain(self):
        start_string = f'omi_read(27, {self._direction}, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[27, self._direction, 0])
        gain_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        gain = gain_value / 10
        return gain

    def get_tilt(self):
        start_string = f'omi_read(28, {self._direction}, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[28, self._direction, 0])
        tilt_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        tilt = tilt_value / 10
        return tilt

    def get_input_power(self):
        if self._direction == 1:
            value = 41
        else:
            value = 43
        start_string = f'omi_read({value}, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[value, 1, 0])
        input_power_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        input_power = input_power_value / 10
        return input_power

    def get_output_power(self):
        if self._direction == 1:
            value = 42
        else:
            value = 44
        start_string = f'omi_read({value}, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[value, 1, 0])
        output_power_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        output_power = output_power_value / 10
        return output_power

    def get_tot_signal_out_power(self):
        start_string = 'omi_read(42, 2, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[42, 2, 0])
        tot_signal_out_power_value = float(
            get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        tot_signal_out_power = tot_signal_out_power_value / 10
        return tot_signal_out_power

    def get_noise_figure(self):
        return

    def get_voa(self):
        start_string = 'omi_read(29, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[29, 1, 0])
        attenuation_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        attenuation = attenuation_value / 10
        return attenuation

    def set_mode(self, mode):
        if mode.lower() == "constant_current":
            mode_field = 0
        elif mode.lower() == "constant_power":
            mode_field = 1
        elif mode.lower() == "constant_gain":
            mode_field = 2
        else:
            logging.exception(f'Wrong mode code {mode}.')
        self._omi_write(21, 1, 1, 1, mode_field)

    def set_gain(self, gain):
        gain = int32(gain * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(27, self._direction, 1, 1, gain)

    def set_security(self, security):
        self._omi_write(55, self._direction, 1, 1, security)

    def set_current(self, current1, current2):
        current1 = int32(current1 * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(24, 1, 1, 1, current1)
        current2 = int32(current2 * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(24, 2, 1, 1, current2)

    def set_tilt(self, tilt):
        tilt = int32(tilt * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(28, self._direction, 1, 1, tilt)

    def set_output_power(self, power):
        power = int32(power * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(42, 2, 1, 1, power)

    def set_voa(self, attenuation):
        attenuation = int32(attenuation * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(29, 1, 1, 1, attenuation)

    # TODO: TBI
    # def set_apr(self, apr):
    #     pass


class CiscoWSS(AmplifierOmiInterface):
    def __init__(self, **kwargs):
        # refactor
        amp_params = AmplifierInterfaceParams(
            ip_address=kwargs.get("ip_address"),
            port=kwargs.get("port"),
            username=kwargs.get("username"),
            password=kwargs.get("password"),
            protocol=kwargs.get("protocol")

        )
        amp_int = AmplifierInterface(amp_params)
        amp_int.login()
        self._switch = kwargs.get("switch")
        super().__init__(amp_int.socket)

    def get_ocm(self, port="COM", switch="MUX"):

        reg_dmx = range(0, 35, 2)
        reg_mux = range(1, 36, 2)


        if switch == "MUX":
            if port == "COM":
                ocm_bin = self._ocm_raw_read(4096, *[reg_mux[-1]])
            else:
                ocm_bin = self._ocm_raw_read(4096, *[reg_mux[port-1]])
        else:
            if port == "COM":
                ocm_bin = self._ocm_raw_read(4096, *[reg_dmx[-1]])
            else:
                ocm_bin = self._ocm_raw_read(4096, *[reg_dmx[port-1]])

        chs = ocm_bin.split("ch")

        slices = []
        powers = []

        for ch in chs[1:]:
            values = ch.split(",")
            slices.append(int(values[0]))
            powers.append(float(values[1].split("power")[1])/10)

        f_slices = [(191.35 + i*float(0.00625)) for i in slices]
        return f_slices, powers

    def init_channel_WXC(self, channel, freq, bw, att, exp_port=17, switch = "MUX"):
        
        if 1 < freq < 1000:
            f_c = int(freq * 1e3 / 6.25)
        elif 1 < freq / 1e3 < 1000:
            f_c = int(freq / 6.25)
        elif 1 < freq / 1e6 < 1000:
            f_c = int(freq / 1e3 / 6.25)
        elif 1 < freq / 1e9 < 1000:
            f_c = int(freq / 1e6 / 6.25)
        elif 1 < freq / 1e12 < 1000:
            f_c = int(freq / 1e9 / 6.25)
        else:
            raise ValueError("Invalid frequency value")

        print("freq conf:", freq)


        if f_c < 30612 or f_c > 31380:
            print(f"Channel frequency ({f_c * 6.25 / 1e3:.3f} THz) out of range! "
                  "Please select a frequency between 191.325 and 196.125 THz")
            return

        if 1 < bw < 1000:
            bw_c = int(bw / 12.5)
        elif 1 < bw / 1e3 < 1000:
            bw_c = int(bw / 1e3 / 12.5)
        elif 1 < bw / 1e6 < 1000:
            bw_c = int(bw / 1e6 / 12.5)
        elif 1 < bw / 1e9 < 1000:
            bw_c = int(bw / 1e9 / 12.5)
        elif 1 < bw / 1e12 < 1000:
            bw_c = int(bw / 1e12 / 12.5)
        else:
            raise ValueError("Invalid bandwidth value")

        if bw_c < 4 or bw_c > 40:
            print(f"Channel bandwidth ({bw_c * 12.5:.1f} GHz) out of range! "
                  "Please select a bandwidth between 50 and 500 GHz")
            return
        
        # set channel off
        if switch == 'DMX':
            self._omi_write(80, channel, 1, 1, 0)
        elif switch == 'MUX':
            self._omi_write(82, channel, 1, 1, 0)
        else:
            raise ValueError("Invalid MUX_DMX value")
        

        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        # # time.sleep(0.1)

        # assegna frequenza centrale
        if switch == 'DMX':
            self._omi_write(28, channel, 1, 1, f_c)
        elif switch == 'MUX':
            self._omi_write(34, channel, 1, 1, f_c)


        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        time.sleep(0.1)

        # banda intorno al canale centrale (in numero di slot da 12.5)
        if switch == 'DMX':
            self._omi_write(29, channel, 1, 1, bw_c)
        elif switch == 'MUX':
            self._omi_write(35, channel, 1, 1, bw_c)
        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        time.sleep(0.1)
        #

        # init optical port
        if switch == 'DMX':
            self._omi_write(27, channel, 1, 1, exp_port)
        elif switch == 'MUX':
            self._omi_write(33, channel, 1, 1, exp_port)
        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        time.sleep(0.1)

        # voa mode in modo che posso passare att e non potenzaq
        if switch == 'DMX':
            self._omi_write(26, channel, 1, 1, 1)
        elif switch == 'MUX':
            self._omi_write(32, channel, 1, 1, 1)
        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        time.sleep(0.1)

        # set att
        if switch == 'DMX':
            self._omi_write(30, channel, 1, 1, int(att * 10))
        elif switch == 'MUX':
            self._omi_write(36, channel, 1, 1, int(att * 10))
        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        time.sleep(0.1)

        # again
        if switch == 'DMX':
            self._omi_write(26, channel, 1, 1, 1)
        elif switch == 'MUX':
            self._omi_write(32, channel, 1, 1, 1)
        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)
        time.sleep(0.1)

        # on
        if switch == 'DMX':
            self._omi_write(80, channel, 1, 1, 1)
        elif switch == 'MUX':
            self._omi_write(82, channel, 1, 1, 1)
        # WXC.write(command.encode())
        # status = poll(WXC, b':', 5)

        print("Channel set")




            #todo add check on ch set
        # if status == 1:
        #     print(f'{mux_dmx} channel {Channel} correctly switched on')
        # else:
        #     print(f'WARNING: {mux_dmx} channel {Channel} cannot be switched off')

        # time.sleep(0.1)

    # Assuming you have a function "poll" for communication, similar to MATLAB's "poll" function.
    # Make sure to implement it accordingly using the communication method of your choice.

    def set_ch_on(self, ch,switch="MUX"):
        if switch == 'DMX':
            self._omi_write(26, ch, 1, 1, 1)
        elif switch == 'MUX':
            self._omi_write(32, ch, 1, 1, 1)

        time.sleep(1)

        if switch == "DMX":
            value = 80
        else:
            value = 82
        self._omi_write(value, ch, 1, 1, 1)


    def set_ch_off(self, ch, switch="MUX"):
        print("setting channel ", ch, "to off")
        if switch == "DMX":
            value = 80
        else:
            value = 82
        self._omi_write(value, ch, 1, 1, 0)