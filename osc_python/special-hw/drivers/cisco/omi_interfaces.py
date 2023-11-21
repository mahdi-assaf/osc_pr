import time
import logging

import math
from numpy import int32
import sys
from socket import socket
from osi.interface.omi.utils import get_string_between
from osi.interface.omi.utils import clear_buffer
from telnetlib import Telnet

TO = 5


class AmplifierOmiInterface:
    def __init__(self, socky: socket):
        self._socket = socky

    @property
    def socket(self):
        return self._socket

    # OMI Commands
    def _omi_read(self, buffer_size: int, *f_list: int):
        fields = get_string_between(str([f for f in f_list]), '[', ']')
        socky = self.socket
        command = f'omi_read({fields})\r'
        command_bytes = command.encode('utf8')
        socky.send(command_bytes)
        time.sleep(0.3)
        value = socky.recv(buffer_size)
        clear_buffer(socky)
        return value

    def _omi_write(self, f0: int, f1: int, f2: int, f3: int, value):
        socky = self._socket
        command = f'omi_write({f0},{f1},{f2},{f3},{value})\r'
        command_bytes = command.encode('utf8')
        socky.send(command_bytes)
        time.sleep(0.3)
        clear_buffer(socky)

    def _ocm_raw_read(self, buffer_size: int, *f_list: int):
        fields = get_string_between(str([f for f in f_list]), '[', ']')
        socky = self.socket
        command = f'ocm_raw_read {fields}\r'
        command_bytes = command.encode('utf8')
        socky.send(command_bytes)
        time.sleep(0.3)
        str_buf = ""
        while not "ch 767" in str_buf:
            value = socky.recv(buffer_size)
            str_buf += str(value).replace("b", "").replace("'",'').replace('"','')
        clear_buffer(socky)
        return str_buf


    def _omi_write_and_check(self):
        pass


class EDFA17OmiInterface(AmplifierOmiInterface):
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
        start_string = 'omi_read(30, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[30, 1, 0])
        gain_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        gain = gain_value / 10
        return gain

    def get_tilt(self):
        start_string = 'omi_read(33, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[33, 1, 0])
        tilt_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        tilt = tilt_value / 10
        return tilt

    def get_input_power(self):
        start_string = 'omi_read(41, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[41, 1, 0])
        input_power_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        input_power = input_power_value / 10
        return input_power

    def get_output_power(self):
        start_string = 'omi_read(42, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[42, 1, 0])
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
        self._omi_write(30, 1, 1, 1, gain)

    def set_current(self, current1, current2):
        current1 = int32(current1 * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(24, 1, 1, 1, current1)
        current2 = int32(current2 * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(24, 2, 1, 1, current2)

    def set_tilt(self, tilt):
        tilt = int32(tilt * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(33, 1, 1, 1, tilt)

    def set_output_power(self, power):
        power = int32(power * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(42, 2, 1, 1, power)

    def set_voa(self, attenuation):
        attenuation = int32(attenuation * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(29, 1, 1, 1, attenuation)

    # TODO: TBI
    # def set_apr(self, apr):
    #     pass


class EDFA35OmiInterface(AmplifierOmiInterface):
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

    def __init__(self, socky: socket, direction: int):
        super().__init__(socky)
        self._direction = direction

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
        start_string = 'omi_read(30, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[30, 1, 0])
        gain_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        gain = gain_value / 10
        return gain

    def get_tilt(self):
        start_string = 'omi_read(33, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[33, 1, 0])
        tilt_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        tilt = tilt_value / 10
        return tilt

    def get_input_power(self):
        start_string = 'omi_read(41, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[41, 1, 0])
        input_power_value = float(get_string_between(mode_bin.decode('utf-8', 'ignore'), start_string, end_string))
        input_power = input_power_value / 10
        return input_power

    def get_output_power(self):
        start_string = 'omi_read(42, 1, 0)\n\rI32-Value is:'
        end_string = '\n\rCompleted'
        mode_bin = self._omi_read(4096, *[42, 1, 0])
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
        self._omi_write(30, 1, 1, 1, gain)

    def set_current(self, current1, current2):
        current1 = int32(current1 * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(24, 1, 1, 1, current1)
        current2 = int32(current2 * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(24, 2, 1, 1, current2)

    def set_tilt(self, tilt):
        tilt = int32(tilt * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(33, 1, 1, 1, tilt)

    def set_output_power(self, power):
        power = int32(power * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(42, 2, 1, 1, power)

    def set_voa(self, attenuation):
        attenuation = int32(attenuation * 10)  # times 10 to have also the first decimal digit, then it rounds to floor
        self._omi_write(29, 1, 1, 1, attenuation)

    # TODO: TBI
    # def set_apr(self, apr):
    #     pass

class WxcOmiInterface():
    """ Interface to the CISCO mainframes.

            Args:
                `ip`: string containing the ip address
                `port`: port on which connection is opened, corresponding to the one on the mainframe where the device is connected
                `username`: username for connecting to the mainframe
                `password`: password for connecting to the mainframe

            Attributes:
                `handle`: Telnet handle for communication

            Methods:
                `login_CISCO`: logs-in at beggining of connection
                `check_connection`: if Telnet connection went down catches error and reconnects
                `reconnect`: re-establish telnet connection
                `close_conn`: closes telnet session
                `send_command`: converts command string in bytes object, sends the command and reads the response
                `_omi_read`: generates omi_read command and sends it
                `_omi_write`: generates omi_write command and sends it
    """

    def __init__(self, ip: str, port: int, username, password, login=True) -> None:
        self.ip = ip
        self.port = port
        self.handle = Telnet(ip, port, timeout=TO)
        self._username = username
        self._password = password
        if login: self.login_CISCO(username, password)

    def login_CISCO(self, username, password):
        """Executes login commands, necessary before the omi_read/write"""
        self.handle.read_until(b':')
        self.handle.write(bytes(username + '\r', 'utf-8'))
        self.handle.read_until(b'Password')
        self.handle.write(bytes(password + '\r', 'utf-8'))
        self.handle.read_eager()

    def check_connection(self):
        try:
            self.handle.read_very_eager()
        except EOFError:
            print("Connection was lost, reconnecting...")
            self.reconnect()
            self.login_CISCO(self._username, self._password)

    def reconnect(self):
        self.handle.open(self.ip, self.port)
        # self.handle.open_port(self.port)

    def close_conn(self):
        """Closes telnet session"""
        self.handle.close()
        self.handle = None

    def send_command(self, command: str, TTL=5):
        """Sends a command string through the Telnet handle defined in the class attributes,
        tries up to `TTL` times if connection was lost or returns a timeout error"""
        self.check_connection()
        self.handle.write(bytes(command, 'utf-8'))
        try:
            answ = self.handle.read_until(b'->', timeout=TO)
        except EOFError:
            if TTL == 0:
                # self.handle.close()
                raise TimeoutError(f"Could not send command '{command}', timed-out")
            answ = self.send_command(command, TTL - 1)
        finally:
            answ = answ.decode()
            if 'err' in answ:
                print(f"WARNING: {answ}")
            return answ

    def _omi_read(self, *f_list: int):
        fields = get_string_between(str([f for f in f_list]), '[', ']')
        command = f'omi_read({fields})\n'
        ans = self.send_command(command)
        return ans

    def _omi_write(self, f0: int, f1: int, f2: int, f3: int, value):
        command = f'omi_write({f0},{f1},{f2},{f3},{value})\n'
        ans = self.send_command(command)
        return ans
