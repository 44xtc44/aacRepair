##################################################################################
#   MIT License
#
#   Copyright (c) [2021] [René Horn]
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
###################################################################################
""" module repairs aac and aacPlus files,
browser get stuck if aac is defective and will not play, also in a playlist
module must know where to store the repaired files, it creates an "aac_repair" folder
and (over)writes a log in this folder, log is printed on stdout

usage:
   Instantiate AacRepair class with one or two arguments. Folder path is mandatory!
   1. Dictionary of files is provided. Folder path is used to store repaired files.
   aac_rep = AacRepair(export_path, file_dict)
   2. No dictionary provided. Folder path is used as list to import files into a dictionary AND store repaired files.
   aac_rep = AacRepair("/home/Kitty/aac_files")

web server:
   web server endpoint converts uploaded files from file storage type to bytestream .read() function
   List of files is written to dictionary {file_name_key: file_byte_content_value}
   {file(n).aac: b'\x65\x66\x67\x00\x10\x00\x00\x00\x04\x00'}
   files = request.files.getlist('fileUploadAcpRepair')
   f_dict = {f.filename: f.read() if f.filename[-5:] == ".aacp" or f.filename[-4:] == ".aac" else None for f in files}
   aac_rep = AacRepair("/home/Kitty/aac_files", f_dict)
   aac_rep.repair()

File system:
   aac_rep = AacRepair(export_path, f_dict)
   aac_rep.repair()

Technical
   aac files use obviously a header (hex fff1) to divide segments / payloads
   we convert the file to hex string (list) to apply a search frame (list) [f,f,f,1]
   start file[0:4], shift search frame file[1:5], file[2:6]
   head cut from the start of first header ...[fff1 file]
   tail cut (head cut to the toes) until the beginning of last header [file]fff1...
"""

import os
import pathlib
import concurrent.futures


class AacRepair:
    """write repaired aac or aac(plus) files from uploaded dictionary of files to disk
    write log list to disk, have line breaks
    calculate cut off bytes to show in the result
    """

    def __init__(self, folder, file_dict=None):
        """ required positional argument folder """
        self.folder = folder
        self.file_dict = file_dict
        self.export_path = os.path.join(self.folder, "aac_repair")
        self.log_list = []
        self.file_size_dict = {}
        self.file_size_rep_dict = {}
        self.repaired_dict = {}
        self.error_dict = {}
        self.file_dict_from_folder()

    def file_dict_from_folder(self):
        """ create dictionary for the repair method from folder, OR
        take an existing dictionary (prepared by web server, no file path, only file name)
        create the export folder for repaired files
        """
        files = []
        aac_folder = pathlib.Path(self.folder)
        for file in aac_folder.iterdir():
            if file.is_file():
                files.append(str(file))
        if self.file_dict is None:
            self.file_dict = {f: open(f, "rb").read() if f[-5:] == ".aacp" or f[-4:] == ".aac" else None for f in files}
        self.make_dirs(self.export_path)

    @staticmethod
    def make_dirs(path):
        try:
            os.makedirs(path, exist_ok=True)
            print(f"\t{path} created")
        except OSError:
            print(f"\tDirectory {path} can not be created\nExit")
            return

    def repair(self):
        """ call repair function
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.repair_one_file, name, content) for name, content in self.file_dict.items()]
            concurrent.futures.wait(futures)

        self.log_writer()
        return

    def repair_one_file(self, file_name, file_content):
        """ repair beginning of file, repair end of file (file content is dictionary value)
        write repaired file (content) to export folder and an entry to the 'repaired_dict'
        """
        tail_repaired = None

        head_repaired = self.tool_aacp_repair_head(file_name, file_content)
        if head_repaired is not None:
            tail_repaired = self.tool_aacp_repair_tail(file_name, head_repaired)

        name_head, name_tail = os.path.split(file_name)
        file_path = os.path.join(self.export_path, name_tail)
        if tail_repaired is not None:
            with open(file_path, 'wb') as binary_writer:
                binary_writer.write(tail_repaired)

            self.repaired_dict[file_name] = file_name
        return True

    def tool_aacp_repair_head(self, f_name, chunk):
        """return bytes slice from shifted start to the end of chunk, except on error
        convert hex and make search string, cut and convert back to bytes

        code
           convert data stream to hex and create search string, direction left to right,
           use index from begin of file, hex_chunk[start:end]
           while shifts the search frame one step over the file (list)
           cut out bytes from shifted start to end of file
           convert hex to bytes

        Info:
           The term 'chunk' comes from web server. It is a piece of the byte stream in the buffer.
           chunk[0:4] are the beginning words of the file, convert a word of two byte(8) to hex(16)
        """
        self.file_size_dict[f_name] = len(chunk)
        hex_chunk = chunk.hex()
        start, end = 0, 4
        search_string = "fff1"
        while 1:
            if end > len(hex_chunk):
                break
            if hex_chunk[start:end] == search_string:
                try:
                    return bytes.fromhex(hex_chunk[start:])
                except ValueError as error:
                    message = f'ValueError {error}'
                    self.error_dict[f_name] = message
                    return
                except Exception as error:
                    message = f'unknown error in tool_aacp_repair_head(), {error} ignore it.'
                    self.error_dict[f_name] = message
                    print(message)
                    return
            start += 1
            end += 1
        return

    def tool_aacp_repair_tail(self, f_name, chunk):
        """return bytes slice cut, except on error

        code
           convert data stream to hex and create reversed search string, direction right to left,
           use index from end of file, reverse index hex_chunk[end:start]
           while shifts the search frame one step over the file (list of hex values)
           cut from file start to the beginning of last header (file)[fff1]... hex_chunk[:end]
           means cut out bytes to rightmost begin of search frame
           convert hex to bytes
        """
        hex_chunk = chunk.hex()
        start, end = -1, -5
        search_string = "fff1"
        while 1:
            if end < -(len(hex_chunk)):
                break
            if hex_chunk[end:start] == search_string:
                try:
                    self.file_size_rep_dict[f_name] = len(bytes.fromhex(hex_chunk[:end]))
                    return bytes.fromhex(hex_chunk[:end])
                except ValueError as error:
                    message = f'ValueError {error}'
                    self.error_dict[f_name] = message
                    # ValueError: non-hexadecimal number found in fromhex() arg at position 64805
                    return
                except Exception as error:
                    message = f'unknown error in tool_aacp_repair_tail(), {error} ignore it.'
                    self.error_dict[f_name] = message
                    print(message)
                    return
            start -= 1
            end -= 1
        return

    def log_writer(self):
        """write log list to disk and screen"""
        ok_list = list()
        for f_name, name in self.repaired_dict.items():
            message = f'{name}; cut(bytes): {self.byte_calc(f_name)}'
            ok_list.append(message)

        fail_msg = f'----- {str(len(self.error_dict))} file(s) failed -----'
        ok_msg = f'----- {str(len(self.repaired_dict))} file(s) repaired -----'
        file_path = pathlib.Path(os.path.join(self.export_path, 'aac_repair.txt'))
        with open(file_path, 'w') as text_writer:
            text_writer.write(fail_msg + '\n')
            [text_writer.write(f'{f_name} {err_msg}' + '\n') for f_name, err_msg in self.error_dict.items()]
            text_writer.write(ok_msg + '\n')
            [text_writer.write(f'{line}' + '\n') for line in ok_list]

        self.log_list.append(f'[ COPY(s) in {self.export_path} ]')
        self.log_list.append(fail_msg)
        self.log_list.extend([f'{f_name} {err_msg}' for f_name, err_msg in self.error_dict.items()])
        self.log_list.append(ok_msg)
        self.log_list.extend(ok_list)
        print(*self.log_list, sep="\n")

    def byte_calc(self, f_name):
        """return cut off bytes"""
        try:
            size = self.file_size_dict[f_name] - self.file_size_rep_dict[f_name]
        except Exception as error:
            message = f'error in byte_calc {error}'
            return message
        return f'[{size}]'
