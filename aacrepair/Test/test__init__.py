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
"""Can test multiple files in folder szenario (aac, aacp, non-aac, mini or zero kB files).

Methods:
   @mock.patch('os.makedirs', mock.Mock(return_value=0)) - disable, monkeypatch.setattr does not work with substitute
   test_deactivate_fs_access() - for GitHub actions
   keep_file_dict() - use return instance value of test_deactivate_fs_access()
"""
import os
import pytest
from unittest import mock
from aacrepair import AacRepair


def substitute_write_repaired_file():
    """Not sure if we can write on GitHub actions.
    Todo test writing fs on GitHub actions, either with pytest tmp or regular
    """
    return


def substitute_delete_file_dict():
    """Keep file dictionary for all test runs online."""
    return


class TestAacRepair:
    """Test scenario class AacRepair.

    Test modifies attributes of THE instance. Modified by other methods. Like the real thing.
    """

    @pytest.fixture(autouse=True)
    @mock.patch('os.makedirs', mock.Mock(return_value=0))
    def init_aac_no_fs(self):
        """Should not write on fs to get this guy working on GitHub actions.

        monkeypatch substitute ignores os.makedirs, it will be exectuted, use mock
        autouse to keep instance alive over tests

        Attributes:
           test_repair_one_file_run_count . Counter to prove synthetic modified file size, compare dict values thingy.
        """
        aac_file_dir = "aac_file"
        this_dir = os.path.dirname(os.path.abspath(__file__))
        test_files_path = os.path.join(this_dir, aac_file_dir)
        self.init_aac_no_fs = AacRepair(test_files_path)     # initialize with folder to read files
        self.repair_one_file_max_loop = 1

    @pytest.fixture
    def deactivate_fs_access(self, monkeypatch):
        monkeypatch.setattr(self.init_aac_no_fs, 'write_repaired_file', substitute_write_repaired_file)

    @pytest.fixture
    def keep_file_dict(self, monkeypatch):
        monkeypatch.setattr(self.init_aac_no_fs, 'delete_file_dict', substitute_delete_file_dict)

    def aac_path_content_get(self, damage=None):
        """Return generator object as (path, content) tuple."""
        if damage:
            self.aac_hair_cut_pedicure()
            for path, size in self.init_aac_no_fs.file_size_dict.items():
                if size:
                    assert self.init_aac_no_fs.file_size_rep_dict[path] < self.init_aac_no_fs.file_size_dict[path]

        key_list = [file_name for file_name in self.init_aac_no_fs.file_dict.keys()]
        value_list = [file_content for file_content in self.init_aac_no_fs.file_dict.values()]
        for i, t in enumerate(zip(key_list, value_list)):
            yield t

    def test_repair_head(self, deactivate_fs_access, keep_file_dict):
        """Start bytes of file must be aac header string fff1."""
        path_content_gen = self.aac_path_content_get()
        while 1:
            try:
                row_column = next(path_content_gen)
            except StopIteration:
                break
            path = row_column[0]
            content = row_column[1]

            cut = self.init_aac_no_fs.repair_head(path, content)
            if cut:
                assert cut[0:2].hex() in ["fff9", "fff1"]
                self.init_aac_no_fs.repaired_dict[path] = path
            else:
                self.init_aac_no_fs.error_dict[path] = path
                pass

    def test_repair_tail(self, deactivate_fs_access, keep_file_dict):
        """Garbage data start bytes must be aac header string fff1.

        Function has two return values. body and tail.
        Tail is the last aac header with (assumed) garbage payload of the file.
        Tail is only for testing.
        """
        path_content_gen = self.aac_path_content_get()
        while 1:
            try:
                row_column = next(path_content_gen)
            except StopIteration:
                break
            path = row_column[0]
            content = row_column[1]

            cut = self.init_aac_no_fs.repair_tail(path, content)
            if cut:
                tail = cut[1]
                assert tail[0:2].hex() in ["fff9", "fff1"]
                self.init_aac_no_fs.repaired_dict[path] = path
            else:
                self.init_aac_no_fs.error_dict[path] = path
                pass

    def test_repair_one_file(self, deactivate_fs_access, keep_file_dict, max_loop=0):
        """Assert file head and cut off of file end (garbage) has aac header string in one action.

        Recursion of test with synthetic damaged file content.
        """
        if max_loop > self.repair_one_file_max_loop:
            return

        path_content_gen = self.aac_path_content_get() if not max_loop else self.aac_path_content_get(damage=True)
        while 1:
            try:
                row_column = next(path_content_gen)
            except StopIteration:
                break
            path = row_column[0]
            content = row_column[1]

            file_head = self.init_aac_no_fs.repair_head(path, content)
            if file_head:
                rv = self.init_aac_no_fs.repair_tail(path, content)
                if rv:
                    tail = rv[1]
                    assert tail[0:2].hex() in ["fff9", "fff1"]
                    self.init_aac_no_fs.repaired_dict[path] = path
                    pass
        self.test_repair_one_file(deactivate_fs_access, keep_file_dict, max_loop + 1)

    def test_byte_calc(self):
        """Test byte_calc() with zero values, one test file is empty. Needs before and after value for calc."""
        for path, content in self.init_aac_no_fs.file_dict.items():
            file_content = content
            self.init_aac_no_fs.file_size_dict[path] = len(file_content)
            self.init_aac_no_fs.file_dict[path] = file_content[2:-2]     # file_content[10:-10]
            self.init_aac_no_fs.file_size_rep_dict[path] = len(self.init_aac_no_fs.file_dict[path])
            assert self.init_aac_no_fs.byte_calc(path) > 0

    def aac_hair_cut_pedicure(self):
        """Damage the beginning and end of all files in, from fs loaded, dictionary
        by cutting 2 index of head and tail.
        """
        for path, content in self.init_aac_no_fs.file_dict.items():
            file_content = content
            self.init_aac_no_fs.file_size_dict[path] = len(file_content)
            self.init_aac_no_fs.file_dict[path] = file_content[2:-2]
            self.init_aac_no_fs.file_size_rep_dict[path] = len(self.init_aac_no_fs.file_dict[path])
