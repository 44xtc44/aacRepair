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
import pytest
from unittest import mock
from aacrepair import AacRepair


def substitute_write_repaired_file(foo, bar):
    return


def substitute_delete_file_dict():
    return


@pytest.fixture
@mock.patch('os.makedirs', mock.Mock(return_value=0))
def init_aac_no_fs():
    """Should not write on fs to get this guy working on GitHub actions.

    monkeypatch substitute ignores os.makedirs, it will be exectuted, use mock
    """
    aac_repair = AacRepair(r'.\aac_file')   # initialize with folder to read files
    return aac_repair


@pytest.fixture
def deactivate_fs_access(monkeypatch, init_aac_no_fs):
    monkeypatch.setattr(init_aac_no_fs, 'write_repaired_file', substitute_write_repaired_file)


@pytest.fixture
def keep_file_dict(monkeypatch, init_aac_no_fs):
    monkeypatch.setattr(init_aac_no_fs, 'delete_file_dict', substitute_delete_file_dict)


def aac_path_content_get(init_aac_no_fs):
    """Return generator object of path and content for each iteration.

    Caller must unpack generator return value

    Yield:
       aac_path_content_get() returns object with file path, content; inside single row of multidimensional array.
    """
    key_list = [file_name for file_name in init_aac_no_fs.file_dict.keys()]
    value_list = [file_content for file_content in init_aac_no_fs.file_dict.values()]
    for i, t in enumerate(zip(key_list, value_list)):
        yield t


def test_repair_one_file(init_aac_no_fs, deactivate_fs_access, keep_file_dict):
    """Assert file head and cut off of file end (garbage) has aac header string."""
    generator_row = list(aac_path_content_get(init_aac_no_fs))
    row_column = generator_row[0]
    row_col_path = row_column[0]
    row_col_content = row_column[1]

    path = row_col_path
    content = row_col_content
    file_head = init_aac_no_fs.tool_aacp_repair_head(path, content)
    if file_head is not None:
        if file_head:
            assert file_head[0:2].hex() == "fff1"
            file_body, file_end = init_aac_no_fs.tool_aacp_repair_tail(path, content)
            if file_end is not None:
                assert file_end[0:2].hex() == "fff1"
        else:
            assert init_aac_no_fs.file_size_dict[path] < 2


def test_damage_all_files(init_aac_no_fs, deactivate_fs_access, keep_file_dict):
    """Damage the beginning and end of all files in, from fs loaded, dictionary
    by cutting 10 index steps (* 4 bytes) of head and tail.

    Methods:
       byte_calc() length of file content is larger before cutting, method must handle error if length is zero
       test_repair_one_file() one more test with obviously damaged files
    """
    for path, content in init_aac_no_fs.file_dict.items():
        file_content = content
        init_aac_no_fs.file_size_dict[path] = len(file_content)
        init_aac_no_fs.file_dict[path] = file_content[10:-10]
        init_aac_no_fs.file_size_rep_dict[path] = len(init_aac_no_fs.file_dict[path])

        assert init_aac_no_fs.byte_calc(path) > 0
        test_repair_one_file(init_aac_no_fs, deactivate_fs_access, keep_file_dict)
