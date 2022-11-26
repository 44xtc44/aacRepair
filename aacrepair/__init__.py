##################################################################################
#   MIT License
#
#   Copyright (c) [2022] [René Horn]
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
"""Module repairs aac or aacPlus file objects. Stores on disk or returns in memory.

technical::

   AAC file wants a nice head and tail.
   AAC header starts hex fff(1) or (9), mpeg-(4) or (2)
   Create a header search frame binary b'\xff\xf1', hex fff1
   Move the header search frame over the AAC file.
   Search start is file[0:2] bytes, shift the search frame file[1:3], file[2:4]
   AAC head: remove the first defective frame ...[fff1 file]
   AAC tail: remove the last frame with defective payload [file]fff1...
"""

import os
import pathlib
import concurrent.futures


class AacRepair:
    """Write repaired aac or aacPlus file objects to disk or memory.

    __init__

    :params: folder: use folder for dict if file_dict is None, else is export_path
    :params: file_dict: {file name or path: content}, folder is export_path
    :methods: file_dict_from_folder: read content of aac files folder into a dict for bulk repair

    Class Methods

    :methods: set_export_path: setter export_path
    :methods: get_export_path: getter export_path
    :methods: file_dict_from_folder: {file_path: content,}
    :methods: make_dirs: create a folder with subfolders
    :methods: repair: threaded call of repair_one_file with path, content args
    :methods: convert_file_like_object: return a bytes type object
    :methods: repair_object: single file or chunk, dispatcher
    :methods: repair_one_file: head and tail repair
    :methods: repair_head: only head
    :methods: repair_tail: only tail
    :methods: log_writer: log_list as result
    :methods: byte_calc: calc cut bytes
    :methods: write_repaired_file: write object to file
    :methods: delete_file_dict: del file_dict
    :methods: all_files_touched: if fail generate report
    :methods: report_skip_list: skipped files not in error_dict; shall reveal module failure
    """

    def __init__(self, folder=None, file_dict=None):
        """Instance dicts can be taken to read error messages ``error_dict`` and/or create a report.
        folder is mandatory if class gets arguments.
        """
        self.log_list = []  # for result print (list for JS to stack colored <div>)
        self.skip_list = []  # some file names not touched (len(file_dict) != len(repaired_dict ) + len(error_dict))
        self.error_dict = {}  # { /foo/file.aac: error message}
        self.repaired_dict = {}  # names of successful repaired aac files
        self.file_size_dict = {}  # file size before cut
        self.file_dict = file_dict  # optional dictionary of already prepared aac files {/home/foo.aac:b'\x65\x66\x6',}
        self.file_size_rep_dict = {}  # file size after cut
        self.export_path = ""  # must be string
        self.folder = folder  # aac file source folder
        if self.folder:
            self.export_path = os.path.join(self.folder, "aac_repair")  # default export folder
            self.file_dict_from_folder()  # refuses if file_dict is True

    def get_export_path(self):
        """Getter for export_path dir."""
        return self.export_path

    def set_export_path(self, path):
        """Setter for export_path dir attribute."""
        self.export_path = path

    def __repr__(self):
        return f'AacRepair(r"{self.folder}=None", "{self.file_dict}=None")'

    def __str__(self):
        return f'({self.folder},{self.file_dict})'

    def file_dict_from_folder(self):
        """Create dictionary of files {name: content} for the 'repair()' method, bulk repair.

        Class can also use an existing dictionary (prepared by web server multi-file upload)
        """
        if self.file_dict is None:
            files = []
            aac_folder = pathlib.Path(self.folder)
            for file in aac_folder.iterdir():
                if file.is_file():
                    files.append(str(file))
            self.file_dict = {f: open(f, "rb").read() for f in files if f[-5:] == ".aacp" or f[-4:] == ".aac"}

    @staticmethod
    def make_dirs(path):
        """Create folders.

        :param: path: absolute path that can contain subdirectories
        """
        try:
            os.makedirs(path, exist_ok=True)
            print(f"\t{path} created")
        except OSError:
            print(f"\tDirectory {path} can not be created\nExit")

    def repair(self, keep_file_dict=None):
        """Threaded bulk repair from dictionary.

        :params: keep_file_dict: delete the dictionary yourself
        :rtype: True; if keep_file_dict manual ``delete_file_dict``
        :rtype: False; check ``skip_list`` and ``error_dict``, then --> ``delete both``
        """
        if self.export_path:
            self.make_dirs(self.export_path)

        key_list = [file_name for file_name in self.file_dict.keys()]
        value_list = [file_content for file_content in self.file_dict.values()]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.repair_one_file, key_list, value_list)

        got_all_files = self.log_writer()

        if not keep_file_dict:
            self.delete_file_dict()
        return got_all_files

    def convert_file_like_object(self, file_full_name):
        """Read file from file system and return content as bytes type.

        :param: file_full_name: The absolute path to the file
        :exception: write report into error_dict
        :rtype: False
        :return: object type bytes
        """
        try:
            chunk = open(file_full_name, "rb").read()
        except OSError as os_error:
            msg = f'Error in convert_file_like_object(): {os_error}'
            self.error_dict[file_full_name] = msg
            print(msg)
            return False
        self.file_size_dict[file_full_name] = len(chunk)
        return chunk

    def repair_object(self, chunk, head=None, tail=None):
        """Return the repaired binary file object from binary source (buffer) or file content.

        ``file_full_name`` is alias to reuse methods and write to error and info dicts

        :params: chunk: buffer, queue, or file content
        :params: head: of chunk repair
        :params: tail: of chunk repair

        :methods: convert_file_like_object: get file content from path given
        :methods: repair_one_file: one chunk left and right, call repair_head and repair_tail
        :methods: repair_head: left side only
        :methods: repair_tail: right side only

        :rtype: bytes type file object
        :rtype: False; check ``error_dict`` after this method call
        """
        file_full_name = "buf.aac"

        if type(chunk) != bytes:
            chunk = self.convert_file_like_object(chunk)
            if not chunk:
                return False

        if (not head and not tail) or (head and tail):
            body = self.repair_one_file(file_full_name, chunk, skip_write=True)
            rv = body if body else False
            return rv

        if head and not tail:
            nice_head_bad_tail = self.repair_head(file_full_name, chunk)
            rv = nice_head_bad_tail if nice_head_bad_tail else False
            return rv

        if tail and not head:
            tail_rep = self.repair_tail(file_full_name, chunk)
            if tail_rep:
                # tail_end (tail_rep[1]) is needed to test the module
                headless_tail = tail_rep[0]
                return headless_tail
            else:
                return False

    def repair_one_file(self, file_full_name, damaged_data, skip_write=None):
        """Repair the beginning or end of file (damaged_data is dictionary value).

        :params: file_full_name: The absolute path to the file.
        :params: damaged_data: binary file content
        :params: file_full_name: bulk repair, name of export folder
        :params: skip_write: method should not write a file

        :rtype: bytes: binary data: repaired file content
        :rtype: False: read the error dict
        """
        file_name_path, file_name = os.path.split(file_full_name)
        file_export = os.path.join(self.export_path, file_name)

        head_repaired = self.repair_head(file_full_name, damaged_data)
        if head_repaired:
            cut = self.repair_tail(file_full_name, head_repaired)
            if cut:
                # tail (cut[1]) is needed for testing the module
                body = cut[0]
                if not skip_write:
                    self.write_repaired_file(file_export, body)
                else:
                    return body
            else:
                return False
            self.repaired_dict[file_full_name] = file_full_name
        else:
            return False

    def repair_head(self, f_name, chunk):
        """Return bytes content left repaired ...[fff1 file]

        :param: f_name: file name for the error, info dict
        :param: chunk: The data to cut.
        :return: binary data
        :rtype: bytes
        """

        start, end = 0, 2
        header = ["fff9", "fff1"]

        self.file_size_dict[f_name] = len(chunk)
        if len(chunk) < end:
            self.error_dict[f_name] = "File is smaller than aac header search frame - ignore it."
            return

        while 1:
            if end > len(chunk):
                self.error_dict[f_name] = "File has no aac header - ignore it."
                break
            if chunk[start:end].hex() in header:
                try:
                    return chunk[start:]
                except Exception as error:
                    message = f'HEAD unknown error in repair_head(), {error} ignore file.'
                    self.error_dict[f_name] = message

            start += 1
            end += 1

    def repair_tail(self, f_name, chunk):
        """Return bytes content right repaired [file]fff1...

        :param: f_name: file name for the error, info dict
        :param: chunk: The data to cut.
        :return: binary data
        :rtype: bytes
        """
        end, start = -3, -1
        header = ["fff9", "fff1"]
        while 1:
            if end < -(len(chunk)):
                break
            if chunk[end:start].hex() in header:
                try:
                    file_body = chunk[:end]
                    file_end = chunk[end:]
                    self.file_size_rep_dict[f_name] = len(file_body)
                    return file_body, file_end
                except Exception as error:
                    message = f'TAIL unknown error in repair_tail(), {error} ignore file.'
                    self.error_dict[f_name] = message

            start -= 1
            end -= 1

    def log_writer(self):
        """Write available logs to screen and keep it ``log_list`` for later HTML colorized report.

        :rtype: True: ok
        :rtype: False: errors found, or files where skipped due to a program bug
        """
        job_done = self.all_files_touched()
        if len(self.error_dict):
            job_done = False

        ok_list = list()
        for f_name, name in self.repaired_dict.items():
            message = f'{name}; cut(bytes): {self.byte_calc(f_name)}'
            ok_list.append(message)

        ok_msg = f'----- {str(len(self.repaired_dict))} file(s) repaired -----'
        fail_msg = f'----- {str(len(self.error_dict))} file(s) failed -----'
        count_msg = f'----- {str(len(self.file_dict))} file(s) to repair -----'

        self.log_list.append(f'\n[ COPY(s) in {self.export_path} ]\n')
        self.log_list.append(count_msg)
        if not job_done:
            self.log_list.append('----- skipped files -----')
            self.log_list.extend(self.report_skip_list())
        self.log_list.append(fail_msg)
        self.log_list.extend([f'{f_name} {err_msg}' for f_name, err_msg in self.error_dict.items()])
        self.log_list.append(ok_msg)
        self.log_list.extend(ok_list)
        print(*self.log_list, sep="\n")
        return job_done

    def byte_calc(self, f_name):
        """Return number of cut bytes.

        :param: f_name: file path for error, or info dict
        :exception: write error, set size to 1
        :rtype: int

        :return: cut bytes
        :rtype: int
        """
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
    def write_repaired_file(export_path, file_content):
        """Write repaired file content to disk.

        :param: export_path: setter or os.joined default export path
        :param: file_content: bytes type content
        """
        with open(export_path, 'wb') as binary_writer:
            binary_writer.write(file_content)

    def delete_file_dict(self):
        """Outsourced to prevent del dict in test mode."""
        self.file_dict = {}

    def all_files_touched(self):
        """Check for error in module, file failure not written in error_dict.

        :return: False if calc not match, see ``report_skip_list``
        """
        file_ok = len(self.repaired_dict)
        file_all = len(self.file_dict)
        file_fail = len(self.error_dict)
        file_left_behind = file_all - (file_ok + file_fail)
        rv = True if not file_left_behind else False
        return rv

    def report_skip_list(self):
        """all_files_touched sum calc got no match, write file names of skipped files into ``skip_list``

        :return: list of skipped files
        :rtype: list
        """
        fail_list = [file for file in self.error_dict.keys()]
        ok_list = [file for file in self.repaired_dict.keys()]
        ok_list.extend(fail_list)
        self.skip_list = [file for file in self.file_dict.keys() if file not in ok_list]
        return self.skip_list
