"""Output is human-readable. Non-destructive.
Use as input for further aac stream processing.

* check next fame is available
* check if profile changed to low quality stream
* compare sample rates to keep the better stream
* switch the stream url endpoint on low quality, if channel config changed
"""
from aacrepair import audio_conf, crc


def header_info(aac_object, frame_bytes=None, print_out=None):
    """Caller can name a slice of the object ``aac_object[start idx:]`` to work.
    Example how to move the header_info in ``header_aac.read_all_header()``.

    :param: aac_object: full object or slice
    :param: frame_bytes: dump whole frame to header_dict['FRAME_BYTES']
    :param: print_out: enable print to screen

    :return: frame header properties
    :rtype: dict
    """
    # 7 Bytes of obj; loop over Byte, bin() out is string plus lead '0b', remove '0b' fill 0's left to get an 8 row
    header_bit_str_list = [(bin(bits)[2:].zfill(8)) for bits in aac_object[:7]]
    h_bit_str = ''.join(header_bit_str_list)

    sync_word = all([int(bit) for bit in h_bit_str[:12]])  # list of 'True' here 1; must contain int or bool
    if not sync_word:
        return False

    # get next header start bytes
    try:
        frame_length = int(h_bit_str[30:43], 2)
    except ValueError:
        return False
    header = ['fff1', 'fff9']  # 0|001   1|001   1, 9   mpeg-4 , mpeg-2
    next_frame_start_bytes = aac_object[frame_length:frame_length + 2]
    is_last_frame = True if not next_frame_start_bytes.hex() in header else False
    crc_bool = True if h_bit_str[15:16] == '0' else False   # --> trip wire, bit is set 1 for no CRC

    crc_16_sum_dict = {}
    if crc_bool:
        crc_byte_list = [
            aac_object[7:8],
            aac_object[8:9],
        ]
        crc_16_sum_dict = crc.reveal_crc(crc_byte_list)

    profile = int(h_bit_str[16:18], 2)
    sampling = int(h_bit_str[18:22], 2)
    channel = int(h_bit_str[23:26], 2)

    header_dict = {
        "SYNC_WORD_BOOL": sync_word,
        "MPEG4_BOOL": True if h_bit_str[12:13] == '0' else False,  # mpeg-4 is set 0
        "Layer_BOOL": True if h_bit_str[13:15] == '1' else True,  # must be 0
        "CRC_16_IS_SET_BOOL": crc_bool,
        "PROFILE_INT": profile,
        "PROFILE_STR": audio_conf.profile[profile],  # 3: AAC SSR (Scalable Sample Rate)
        "SAMPLING_FREQUENCY_INT": sampling,
        "SAMPLING_FREQUENCY_STR": audio_conf.sampling[sampling],  # 3: 48000 Hz
        "PRIVATE_BIT_BOOL": True if h_bit_str[22:23] == '1' else False,  # must be 0
        "CHANNEL_CONFIG_INT": channel,
        "CHANNEL_CONFIG_STR": audio_conf.channel[channel],  # 2: 2 channels: front-left, front-right
        "ORIGINALITY_BOOL": True if h_bit_str[26:27] == '1' else False,
        "HOME_BOOL": True if h_bit_str[27:28] == '1' else False,
        "COPYRIGHT_ID_INT": int(h_bit_str[28:29]),
        "COPYRIGHT_START_INT": int(h_bit_str[29:30]),
        "FRAME_LENGTH_INT": frame_length,
        "BIT_RESERVOIR_INT": int(h_bit_str[43:54], 2),
        "FRAME_NUMBER_INT": int(h_bit_str[54:56], 2),
        "CRC_16": crc_16_sum_dict,
        "IS_LAST_FRAME_BOOL": is_last_frame,
        "ERROR_STR": "",
        "FRAME_BYTES": b'',
    }

    if frame_bytes:
        header_dict['FRAME_BYTES'] = bytearray(aac_object[:header_dict['FRAME_LENGTH_INT']])
        if len(header_dict['FRAME_BYTES']) != header_dict['FRAME_LENGTH_INT']:
            header_dict['ERROR_STR'] = "--> frame length don't match"

    if print_out:
        fh = f'\nFirst Header & crc: {h_bit_str[0:72]}' if crc_bool else f'\nFirst Header: {h_bit_str[0:56]}'
        print(fh)
        print(*[f'{header_prop}: {prop_val} \n' for header_prop, prop_val in header_dict.items()])
        lf = "This is the last frame." if header_dict["IS_LAST_FRAME_BOOL"] else "Not last frame."
        print(lf)

    return header_dict


def header_index_get(aac_object):
    """Scan the file object for an aac frame. Search frame is hex.

    :param: aac_object: bytes
    :return: INDEX number of the first frame start Byte in the stream
    :rtype: int
    """
    start, end = 0, 2
    header = ["fff9", "fff1"]
    while 1:
        if end > len(aac_object):
            return False
        if aac_object[start:end].hex() in header:
            return start
        start += 1
        end += 1


def read_all_header(aac_object, convert_bytes_hex=None):
    """Example function returns all frame content with header until empty.

    :param: aac_object: bytes type object
    :param: convert_bytes_hex: for cut-and-paste into checksum calculator

    :return: header information and object content
    :rtype: Iterator[`dict`]
    """
    if aac_object != type(bytes):
        aac_object = open(aac_object, "rb").read()

    start = header_index_get(aac_object)
    if not start:
        return

    checked = start
    while 1:
        h_dict = header_info(aac_object[checked:], frame_bytes=True, print_out=None)
        if not h_dict:
            break
        checked += h_dict['FRAME_LENGTH_INT']
        h_dict['FRAME_BYTES'] = bytearray(aac_object[checked:checked + h_dict['FRAME_LENGTH_INT']])

        if convert_bytes_hex:
            bytes_to_hex = h_dict['FRAME_BYTES']
            h_dict['FRAME_BYTES'] = bytearray(bytes_to_hex).hex()
        yield h_dict


def pull_frame(path_str=None):
    """Example to get the header and all frames of the object (file content).

    :param: path_str: file path or object
    """
    if not path_str:
        path_str = r'f:\10\foo.aac'

    gen = read_all_header(path_str, convert_bytes_hex=True)
    for row in list(gen):
        print(row)


def main():
    pull_frame()


if __name__ == '__main__':
    main()
