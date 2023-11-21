from pandas import DataFrame
from pathlib import Path
import logging
import json
from osi.interface.omi.params import ChassisInterfaceParams, AmplifierInterfaceParams
from osi.interface.omi.user import ChassisInterface


# TODO: to replace in params.py?
class ControllerParams:

    def __init__(self, ip_port_edfa: DataFrame, credentials: DataFrame, protocol: str):
        self._ip_port_edfa = ip_port_edfa
        self._credentials = credentials
        # TODO: restructure protocol capture
        self._protocol = protocol

    @property
    def ip_port_edfa(self):
        return self._ip_port_edfa

    @property
    def credentials(self):
        return self._credentials

    @property
    def protocol(self):
        return self._protocol


class Controller:

    def __init__(self, params: ControllerParams, network_description=None):
        self._params = params
        self._chassis = {}
        self._configure_chassis()
        self._network_description = network_description

    @property
    def params(self):
        return self._params

    @property
    def chassis(self):
        return self._chassis

    @property
    def network_description(self):
        return self._network_description

    @network_description.setter
    def network_description(self, network_description):
        elements = network_description['elements']
        for el in elements:
            if 'operational' in el:
                el.pop('operational')
        self._network_description = network_description

    def network_description_to_json(self, file_name):
        network_description = self.network_description
        json.dump(network_description, file_name)

    def _configure_chassis(self):
        ip_port_edfa = self.params.ip_port_edfa
        credentials = self.params.credentials
        protocol = self.params.protocol

        for ip_addr in ip_port_edfa.ip_address.unique():
            chassis_cred = credentials[credentials.ip_address == ip_addr].iloc[0]
            chassis_params = ChassisInterfaceParams(ip_addr, chassis_cred.username, chassis_cred.password, protocol)
            chassis_interface = ChassisInterface(chassis_params)
            for _, amp in ip_port_edfa[ip_port_edfa.ip_address == ip_addr].iterrows():
                amp_name = amp.uid
                amp_port = amp.port_number
                amp_params = AmplifierInterfaceParams(ip_addr, amp_port, chassis_cred.username, chassis_cred.password, protocol, amp_name)
                chassis_interface.add_amplifier(amp_params)

            self._chassis[ip_addr] = chassis_interface
        return

    def configure_amplifiers(self, network_description: dict):
        chassis = self.chassis
        elements = network_description['elements']
        for ip_address, cha in chassis.items():
            cha.login()
            for edfa_uid, amp in cha.amplifiers.items():

                filtered_elem = list(filter(lambda elem: elem['uid'] == edfa_uid, elements))

                if len(filtered_elem) == 0:
                    logging.exception(f'{edfa_uid} is not present in the network description')
                elif len(filtered_elem) > 1:
                    logging.exception(f'{edfa_uid} defined multiple times in the network description')

                el = filtered_elem[0]

                operational = el['operational']
                amp.login()
                amp.configure_operational(operational)

                mode = amp.get_mode()
                if mode == 'constant_gain':
                    logging.info(f'Gain target = {operational["gain_target"]:.1f}; actual gain {amp.get_gain()}')
                    logging.info(f'Tilt target = {operational["tilt_target"]:.1f}; actual tilt {amp.get_tilt()}')
                elif mode == 'constant_power':
                    logging.info(f'Pout target = {operational["pout_target"]:.1f}; actual power {amp.get_output_power()}')
                    logging.info(f'Tilt target = {operational["tilt_target"]:.1f}; actual tilt {amp.get_tilt()}')

                amp.close()
            cha.close()

        self.network_description = network_description
        return

    def read_amplifiers(self):
        chassis = self.chassis
        amp_all = ''
        for _, cha in chassis.items():
            print(cha)
            for _, amp in cha.amplifiers.items():
                amp.login()
                amp_string = str(amp)
                amp_all += amp_string + '\n'
                print(amp_string)
                amp.close()
        return amp_all

    def get_configuration(self):
        network_description = self.network_description
        chassis = self.chassis
        elements = network_description['elements']
        for ip_address, cha in chassis.items():
            cha.login()
            for edfa_uid, amp in cha.amplifiers.items():

                filtered_elem = list(filter(lambda elem: elem['uid'] == edfa_uid, elements))

                # Check if EDFA is missing or multiple in `ip_port_edfa`
                if len(filtered_elem) == 0:
                    logging.exception(f'{edfa_uid} is not present in the network description')
                elif len(filtered_elem) > 1:
                    logging.exception(f'{edfa_uid} defined multiple times in the network description')

                amp.login()
                gain_target = amp.get_gain()
                tilt_target = amp.get_tilt()

                el = filtered_elem[0]
                el['operational'] = {'gain_target': gain_target,
                                     'tilt_target': tilt_target}

                amp.close()
            cha.close()

        return network_description

    def configuration_to_json(self, file_name):
        network_description = self.get_configuration()
        with open(Path(file_name), 'w') as file:
            json.dump(network_description, file, indent=4)

