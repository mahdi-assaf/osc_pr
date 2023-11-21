from time import sleep


def read_buf(shell, buf_size=9999, sleep_time=0.2):
    while not shell.recv_ready():
        sleep(sleep_time)
    out = shell.recv(buf_size).decode('ascii')
    return out


def split_string(string):
    """
    Split a string of a number and a unit of measurement into a tuple of the number and the unit.
    """
    import re
    # split the string using regular expressions to match the number and the unit separately
    num_unit_tuple = re.findall(r'(-?\d+\.?\d*)([a-zA-Z]+)', string)
    if len(num_unit_tuple) == 0:
        return string
    # convert the first element of the tuple (the number) to a float if it contains a decimal, an integer otherwise
    num = float(num_unit_tuple[0][0]) if '.' in num_unit_tuple[0][0] else int(num_unit_tuple[0][0])
    unit = num_unit_tuple[0][1]
    return num, unit

