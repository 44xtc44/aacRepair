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
"""Module stores repaired copies of aac and aacPlus files in the ``aac_repair`` folder.

Browser audio gets stuck if aac is defective and will not play, also in a playlist.

usage:
   Instantiate AacRepair class with one or two arguments. Folder path is mandatory!

   * Dictionary of files is provided. Folder path is used to store repaired files.
      * aac_rep = AacRepair(export_path, file_dict)
   * No dictionary provided. Folder path is used as list to import files into a dictionary AND store repaired files.
      * aac_rep = AacRepair("/home/Kitty/aac_files")

Web server:
   (Flask tested) web server endpoint converts uploaded files from file storage type to bytestream .read() function
   List of files is written to dictionary {file_name_key: file_byte_content_value}
   {file(n).aac: b'\x65\x66\x67\x00\x10\x00\x00\x00\x04\x00'}
   files = request.files.getlist('fileUploadAcpRepair')
   f_dict = {f: open(f, "rb").read() for f in files if f[-5:] == ".aacp" or f[-4:] == ".aac"}
   aac_rep = AacRepair(export_path, f_dict)
   aac_rep.repair()

File system:
   aac_rep = AacRepair(aac_files_folder)
   aac_rep.repair()

technical stuff:
   aac files use a header to divide segments / payloads, (part of header is hex fff1)
   Create a header search frame binary b'\xff\xf1', hex fff1
   Move the header search frame over the aac file
   start is file[0:2], shift the search frame file[1:3], file[2:4]
   aac file head: remove the first defective! payload ...[fff1 file]
   aac file tail: remove the last header with defective? payload [file]fff1...
"""

import os
import pathlib
import concurrent.futures


class AacRepair:
    """Write repaired aac or aac(plus) files from a dictionary of files to disk.

    calculate number of cut bytes and show it in the result
    """

    def __init__(self, folder, file_dict=None):
        """Instance dictionaries can be taken to create a report later.

        Method:
           file_dict_from_folder() read content of aac files into a dict and create export folder
        """
        self.folder = folder                                        # aac file folder
        self.export_path = os.path.join(self.folder, "aac_repair")  # repaired file store, can get monkey patch
        self.file_dict = file_dict                                  # optional dictionary of already prepared aac files
        self.file_size_dict = {}                                    # original file size
        self.file_size_rep_dict = {}                                # file size after cut
        self.repaired_dict = {}                                     # names of successful repaired aac files
        self.error_dict = {}                                        # {aac file: error message}
        self.log_list = []                                          # for printing (list for JS to stack colored <div>)
        self.skip_list = []                                         # files not touched for some reason, inspect later
        self.file_dict_from_folder()

    def file_dict_from_folder(self):
        """Create dictionary of files {name: content} for the repair method.

        Can take an existing dictionary (prepared by web server, no file path, only file name),
        create the export folder for repaired files
        """
        files = []
        aac_folder = pathlib.Path(self.folder)
        for file in aac_folder.iterdir():
            if file.is_file():
                files.append(str(file))
        if self.file_dict is None:
            self.file_dict = {f: open(f, "rb").read() for f in files if f[-5:] == ".aacp" or f[-4:] == ".aac"}
        self.make_dirs(self.export_path)

    @staticmethod
    def make_dirs(path):
        """Create folders."""
        try:
            os.makedirs(path, exist_ok=True)
            print(f"\t{path} created")
        except OSError:
            print(f"\tDirectory {path} can not be created\nExit")

    def repair(self):
        """Repair function is using threads for a bit more speed.

        Returns:
           True if log_writer() get reports of all files
        """
        key_list = [file_name for file_name in self.file_dict.keys()]
        value_list = [file_content for file_content in self.file_dict.values()]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.repair_one_file, key_list, value_list)
        all_files = self.log_writer()
        self.delete_file_dict()
        return all_files

    def repair_one_file(self, file_full_name, damaged_data):
        """Repair the beginning of a file, repair end of file (file content is dictionary value).

        Write the repaired file (content) to export folder and an entry into the 'repaired_dict'.
        """
        file_name_path, file_name = os.path.split(file_full_name)
        file_export = os.path.join(self.export_path, file_name)

        head_repaired = self.repair_head(file_full_name, damaged_data)
        if head_repaired:
            rv = self.repair_tail(file_full_name, head_repaired)
            if rv:
                # tail (garbage) is needed for testing the module
                body, tail = rv[0], rv[1]
                self.write_repaired_file(file_export, body)
                self.repaired_dict[file_full_name] = file_full_name

    def repair_head(self, f_name, chunk):
        """Return bytes from shifted start to the end of chunk, except on error.

        code:
           convert bytes data to hex and create search string, index direction left to right,
           while shifts the search frame one step over the file (list)
           cut bytes from shifted start to end of file

        Return:
           binary data
        """
        start, end = 0, 2
        header = "fff1"

        self.file_size_dict[f_name] = len(chunk)
        if len(chunk) < end:
            self.error_dict[f_name] = "File is smaller than aac header search frame - ignore it."
            return

        while 1:
            if end > len(chunk):
                self.error_dict[f_name] = "File has no aac header - ignore it."
                break
            if chunk[start:end].hex() == header:
                try:
                    return chunk[start:]
                except Exception as error:
                    message = f'HEAD unknown error in repair_head(), {error} ignore file.'
                    self.error_dict[f_name] = message
                    return
            start += 1
            end += 1
        return

    def repair_tail(self, f_name, chunk):
        """Return file content good bytes for writing a new file, except on error.

        code:
           convert data stream to hex and create reversed index, direction right to left,
           while shifts the search frame one step over the file (list of hex values)
           cut good bytes from repaired begin of file to the beginning of last header (file)[fff1...]

        Return:
           binary data
        """
        end, start = -3, -1
        header = "fff1"
        while 1:
            if end < -(len(chunk)):
                break
            if chunk[end:start].hex() == header:
                try:
                    file_body = chunk[:end]
                    file_end = chunk[end:]
                    self.file_size_rep_dict[f_name] = len(file_body)
                    return file_body, file_end
                except Exception as error:
                    message = f'TAIL unknown error in repair_tail(), {error} ignore file.'
                    self.error_dict[f_name] = message
                    return
            start -= 1
            end -= 1
        return

    def log_writer(self):
        """Write log list to screen and keep it for later HTML colorized report."""
        ok_list = list()
        job_done = self.all_files_touched()

        for f_name, name in self.repaired_dict.items():
            message = f'{name}; cut(bytes): {self.byte_calc(f_name)}'
            ok_list.append(message)

        fail_msg = f'----- {str(len(self.error_dict))} file(s) failed -----'
        ok_msg = f'----- {str(len(self.repaired_dict))} file(s) repaired -----'
        count_msg = f'----- {str(len(self.file_dict))} file(s) to repair -----'

        self.log_list.append(f'\n[ COPY(s) in {self.export_path} ]\n')
        self.log_list.append(count_msg)
        if not job_done:
            self.log_list.append('----- skipped files -----')
            self.log_list.extend(self.all_files_touched(report=True))
        self.log_list.append(fail_msg)
        self.log_list.extend([f'{f_name} {err_msg}' for f_name, err_msg in self.error_dict.items()])
        self.log_list.append(ok_msg)
        self.log_list.extend(ok_list)
        print(*self.log_list, sep="\n")
        return job_done

    def byte_calc(self, f_name):
        """Return number of cut bytes."""
        try:
            size = self.file_size_dict[f_name] - self.file_size_rep_dict[f_name]
            if not size:
                raise Exception('Size: calc result after repair is zero!')
        except Exception as error:
            size = 1
            message = f'Error in byte_calc(): set size to 1 to proceed.(test assert 1>0) {error}'
            self.error_dict[f_name] = message
            return size
        return size

    @staticmethod
    def write_repaired_file(file_path, file_content):
        """Write repaired file content to disk."""
        with open(file_path, 'wb') as binary_writer:
            binary_writer.write(file_content)

    def delete_file_dict(self):
        """Outsourced to prevent del dict in test mode."""
        self.file_dict = {}

    def all_files_touched(self, report=None):
        """Look for files not in result dicts.

        Returns:
           skip_list: list of skipped files if report is requested
        """
        file_fail = len(self.error_dict)
        file_ok = len(self.repaired_dict)
        file_all = len(self.file_dict)
        file_left_behind = file_all - (file_ok + file_fail)
        if report is None:
            if not file_left_behind:
                return True
            else:
                return False

        if report is not None:
            fail_list = [file for file in self.error_dict.keys()]
            ok_list = [file for file in self.repaired_dict.keys()]
            ok_list.extend(fail_list)
            self.skip_list = [file for file in self.file_dict.keys() if file not in ok_list]
            return self.skip_list
