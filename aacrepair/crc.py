"""Should help to read crc bytes and calculate checksum of a container and content.

Place to calculate checksum of Audio container and/or its content.
"""


def reveal_crc(byte_list, print_out=None):
    """Helper to create a function for AAC stream CRC check.
    Calc all possible bit orders, to detect the CRC-CCITT input function pre return options used;
    Normal, reflected and/or reversed.
    Then use either Python CRC check, or a Pypi packet.
    aacrepair.header_aac module can return hex output to put it in an online CRC checker or use fastCRC packet.
    Output must be altered bytes array to slice in the (clean-up before calc) crc sum fields 'ffff', if CRC bit is set.
    Document 'ETSI TS 102 563' section 5.2, Transport of Advanced Audio Coding (AAC) audio; Technical Specification
    Perhaps we can create a software error correction ourselves. Document 'header_firecode', perhaps go from there.

    :params: byte_list: CRC SUM as list of 8 bits of type bytearray or bytes [8], [8,8], [8,8,8,8], [8,8,8,8,8,8,8,8]
    :params: print_out: disable screen printing
    :return: CRC SUM as string, hex and int representation of left right, right left, reversed and flipped bites order
    :rtype: dict
    """
    byte_str_list = []
    for byte in byte_list:
        byte_str_list.append("".join([(bin(bit)[2:].zfill(8)) for bit in byte]))

    bytes_str = "".join(byte_str_list)
    bytes_str_rev = bytes_str[::-1]
    bytes_str_flip = flip_this(bytes_str)
    bytes_str_flip_rev = bytes_str_flip[::-1]

    bytes_hex = '{0:x}'.format(int(bytes_str, 2))
    bytes_hex_rev = '{0:x}'.format(int(bytes_str_rev, 2))
    bytes_hex_flip = '{0:x}'.format(int(bytes_str_flip, 2))
    bytes_hex_flip_rev = '{0:x}'.format(int(bytes_str_flip_rev, 2))

    bytes_int = int(bytes_str, 2)
    bytes_int_rev = int(bytes_str_rev, 2)
    bytes_int_flip = int(bytes_str_flip, 2)
    bytes_int_flip_rev = int(bytes_str_flip_rev, 2)

    check_dict = {
        "crc_list": byte_str_list,
        "str": bytes_str,
        "str_rev": bytes_str_rev,
        "str_flip": bytes_str_flip,
        "str_flip_rev": bytes_str_flip_rev,

        "hex": bytes_hex,
        "hex_rev": bytes_hex_rev,
        "hex_flip": bytes_hex_flip,
        "hex_flip_rev": bytes_hex_flip_rev,

        "int": bytes_int,
        "int_rev": bytes_int_rev,
        "int_flip": bytes_int_flip,
        "int_flip_rev": bytes_int_flip_rev,
    }
    if print_out:
        print(*[f'{header_prop}: {prop_val} \n' for header_prop, prop_val in check_dict.items()])
    return check_dict


def flip_this(bit_str):
    """Complement 1's (flip 0 to 1, 1 to 0) string of bits.

    :param: bit_str: left to right ordered string of all CRC fields
    :return: 1's complement
    :rtype: str
    """
    flip_list = ['1' if bit == '0' else '0' for bit in bit_str]
    return "".join(flip_list)
