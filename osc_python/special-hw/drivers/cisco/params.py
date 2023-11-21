"""
The following module contains all the classes of parameters to be used for the instantiation of the objects
in `interfaces' module.
"""
import logging
from uuid import uuid1


class Tcc2InterfaceParams:
    """ Parameters of the object Tcc2Interface.

    Args:
        ip_address (str): a string with the IP address of the TCC2
        port (int): port number (it should be 23)
        username (bytes): Username to login
        password (bytes): Password to login

    Attributes:
        ip_address (str): store `ip_address`
        port (int): store `port`
        username (bytes): store `username`
        password (bytes): store `password`
    """

    def __init__(self, ip_address: str, port: int, username: str, password: str):
        self._ip_address = ip_address
        self._port = port
        self._username = username.encode()
        self._password = password.encode()

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def port(self):
        return self._port

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password


class AmplifierInterfaceParams:
    """ Parameters of the object AmplifierInterface.

    Args:
        ip_address (str): a string with the IP address of the chassis
        port (int): port number (it is equal to 2000 + the shelf number and it starts from 2001)
        username (bytes): Username to login
        password (bytes): Password to login
        protocol (string): Protocol adopted to communicate with the amplifier. It can be (case insensitive): "omi",
        "tl1"

    Attributes:
        ip_address (str): store `ip_address`
        port (int): store `port`
        username (bytes): store `username`
        password (bytes): store `password`
        protocol (string): store `protocol`
    """

    def __init__(self, ip_address: str, port: int, username: str, password: str, protocol: str,
                 uid: str = str(uuid1())):
        self._uid = uid
        self._ip_address = ip_address
        self._port = port
        self._username = username.encode()
        self._password = password.encode()
        if protocol.lower() != 'omi' and protocol.lower() != 'tl1':
            logging.error(f'{protocol} protocol not implemented.')
        self._protocol = protocol

    def __repr__(self):
        return (f'{type(self).__name__}('
                f'ip_address={repr(self.ip_address)}, '
                f'port={self.port!r}, '
                f'username={self.username!r}, '
                f'protocol={self.protocol!r}, '
                f'uid={self.uid!r})')

    @property
    def uid(self):
        return self._uid

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def port(self):
        return self._port

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def protocol(self):
        return self._protocol


class ChassisInterfaceParams:
    """

    """

    def __init__(self, ip_address: str, username: bytes, password: bytes, protocol: str):
        self._ip_address = ip_address
        self._username = username
        self._password = password
        if protocol.lower() != 'omi' and protocol.lower() != 'tl1':
            logging.error(f'{protocol} protocol not implemented.')
        self._protocol = protocol

    def __str__(self):
        return '\n'.join([f'{type(self).__name__}',
                          f'  ip_address: {self.ip_address}',
                          f'  username:   {self.username}',
                          f'  protocol:   {self.protocol}'])

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def protocol(self):
        return self._protocol


class WxcInterfaceParams:
    """ Parameters of the object Tcc2Interface.

    Args:
        ip_address (str): a string with the IP address of the TCC2
        port (int): port number (it should be 23)
        username (bytes): Username to login
        password (bytes): Password to login

    Attributes:
        ip_address (str): store `ip_address`
        port (int): store `port`
        username (bytes): store `username`
        password (bytes): store `password`
    """

    def __init__(self, ip_address: str, port: int, username: str, password: str):
        self._ip_address = ip_address
        self._port = port
        self._username = username.encode()
        self._password = password.encode()

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def port(self):
        return self._port

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password
