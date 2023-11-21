from socket import socket
import select
from time import sleep


# def clear_buffer(socky: socket):
#     Not working so far
#     data = 'planet'
#     while data:
#         data = socky.recv(1024)
#         sleep(0.1)
def clear_buffer(sock: socket):
    """remove the data present on the socket"""
    while 1:
        inputready, o, e = select.select([sock], [], [], 0.0)
        if len(inputready) == 0:
            break
        for s in inputready:
            s.recv(1)


def get_string_between(string: str, start_string: str, end_string: str):
    """ It extracts from `string` a substring between `start_string` and `end_string`.

    :param string: (string) initial string
    :param start_string: (string) initial limiting string
    :param end_string: (string) final limiting string
    :return: (string) substring between `start_string` and `end_string`
    """
    partial = string.split(start_string)[1]
    return partial.split(end_string)[0]
