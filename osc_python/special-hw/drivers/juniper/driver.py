from paramiko import SSHClient, AutoAddPolicy
from drivers.juniper.utils import read_buf, split_string
from core.constants import *
import drivers.juniper.constants as CONST


GET_CONV = {
    STATE_GAIN: "GainValue",
    STATE_TILT: "TiltValue",
    STATE_INPUT_POWER: "InputTotalPower",
    STATE_OUTPUT_POWER: "OutputTotalPower",
    STATE_SERVICE: "State",
    CONFIG_GAIN: "GainSetPoint",
    CONFIG_TILT: "TiltSetPoint",
    CONFIG_OUTPUT_ENABLED: "OutputEnable",
    CONFIG_RANGE: "GainRange",
    CONFIG_MODE: "Mode"
}

SET_CONV = {
    CONFIG_GAIN: "gain",
    CONFIG_RANGE: "gainrange",
    CONFIG_OUTPUT_ENABLED: "output",
    CONFIG_TILT: "tilt"
}


class JuniperIla:
    def __init__(self, **kwargs):

        self._constants = {}
        direction = kwargs["direction"]

        if isinstance(direction, str) and direction not in ["ab", "ba"]:
            raise IOError("Direction must be ab or ba.")
        elif isinstance(direction, str) and direction in ["ab", "ba"]:
            if direction == "ab":
                self._direction = 1
            else:
                self._direction = 2
        elif isinstance(direction, int) and direction not in [1, 2]:
            raise IOError("Direction must be 1 or 2.")
        else:
            self._direction = direction

        self._hostname = kwargs["hostname"]
        self._port = kwargs["port"]
        self._username = kwargs["username"]
        self._password = kwargs["password"]
        self._edfa_username = kwargs["edfa_username"]
        self._edfa_password = kwargs["edfa_password"]

        # LOGIN
        self._ssh, self._shell = JuniperIla.ssh_connect(self._hostname, self._port, self._username, self._password)
        self.edfa_login(self._shell, self._edfa_username, self._edfa_password)

        self._constants = CONST

    @property
    def constants(self):
        return self._constants

    @staticmethod
    def ssh_connect(hostname, port, username, password):
        # Create an SSH client
        ssh = SSHClient()

        # Automatically add the server's host key
        ssh.set_missing_host_key_policy(AutoAddPolicy())

        # Connect to the SSH server
        ssh.connect(hostname=hostname, port=port, username=username, password=password)

        shell = ssh.invoke_shell()

        read_buf(shell, sleep_time=1)

        return ssh, shell

    def ssh_close(self):
        self._ssh.close()

    def edfa_login(self, shell, edfa_user, edfa_password):
        shell.send("login" + "\n")
        shell.send(edfa_user + "\n")
        shell.send(edfa_password + "\n")
        out = read_buf(shell)

        if "Completed!" not in out:
            print("EDFA shell not active")
            return -1

        print("EDFA login completed:", self._hostname, "on direction:", self._direction)
        return 0

    def get_edfa_info(self):
        self._shell.send("show edfa " + str(self._direction) + "\n")
        out: str = read_buf(self._shell)[:-60] + "\n"
        self._shell.send(" ")
        out += read_buf(self._shell)[6:]
        state = out.split("Edfa")[1]
        config = out.split("Edfa")[2]

        state = state.split('\n')
        state = [el.split(':') for el in state]
        state = [[e.replace("\r", "").replace(" ", "") for e in el] for el in state][1:-2]
        states = {}
        for el in state:
            states[el[0]] = split_string(el[1])

        config = config.split('\n')
        config = [el.split(':') for el in config]
        config = [[e.replace("\r", "").replace(" ", "") for e in el] for el in config][1:-4]
        configs = {}
        for el in config:
            configs[el[0]] = split_string(el[1])
        return states, configs

    def close(self):
        self.ssh_close()

    def get(self, *args):
        state, config = self.get_edfa_info()
        data = {}
        if len(args) == 0:
            inv_map = {v: k for k, v in GET_CONV.items()}
            return {inv_map.get(key, key): value for key, value in (state | config).items()}
        for arg in args:
            label = GET_CONV[arg]
            if label in state.keys():
                data[arg] = state[label]
            if label in config.keys():
                data[arg] = config[label]
        return data

    def get_voa_info(self):
        if self._direction == 1:
            direction = 2
        else:
            direction = 1
        self._shell.send("show evoa " + str(direction) + "\n")
        out: str = read_buf(self._shell)
        state = out.split("Info")[1]
        state = state.split('\n')
        state = [el.split(':') for el in state]
        state = [[e.replace("\r", "").replace(" ", "") for e in el] for el in state][1:-4]
        states = {}
        for el in state:
            states[el[0]] = el[1]
        print(states)

        return states

    def set_voa_att(self, att):
        if self._direction == 1:
            direction = 2
        else:
            direction = 1
        self._shell.send("evoa " + str(direction) + " " + str(att) + "\n")
        read_buf(self._shell)
        self._status.att = att

    def set_gain(self, gain):
        self._shell.send("edfa " + str(self._direction) + " gain " + str(gain) + "\n")
        read_buf(self._shell)

    def set_tilt(self, tilt):
        self._shell.send("edfa " + str(self._direction) + " tilt " + str(tilt) + "\n")
        read_buf(self._shell)

    def set_gainrange(self, gainrange):
        if gainrange not in ["high", "low"]:
            print("Value must be high or low")
            raise IOError
        self._shell.send("edfa " + str(self._direction) + " gainrange " + gainrange + "\n")
        read_buf(self._shell)

    def set_output_enable(self, is_output_enabled):
        if is_output_enabled not in ["disable", "enable"]:
            print("Value must be disable or enable")
            raise IOError
        self._shell.send("edfa " + str(self._direction) + " gainrange " + is_output_enabled + "\n")
        read_buf(self._shell)

    def set(self, **kwargs):
        for arg_key, value in kwargs.items():
            print(f"Setting {arg_key} to {value}")

            command = SET_CONV.get(arg_key)
            if command is None:
                print(f"Warning: {arg_key} is not applicable")
                continue
            value = str(value)
            self._shell.send("edfa " + str(self._direction) + " " + command + " " + value + "\n")
            read_buf(self._shell)


if __name__ == "__main__":
    ila = \
        JuniperIla(
            hostname="192.168.88.36",
            port=22,
            username='admin',
            password='otbu+1',
            edfa_username='WRuser',
            edfa_password='WRuser123',
            direction="ab"
        )

    # print(ila.get_edfa_info())
    print(ila.get("STATE_GAIN"))
    # print(ila.get())
    ila.set(["CONFIG_GAIN", "13"])
    print(ila.get("STATE_GAIN"))
    print(ila.get("CONFIG_GAIN"))

    # ila.set_voa_att(10)
    # ila.get_voa_info()
    # print(ila.get_edfa_info())

