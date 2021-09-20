# Copyright 2021 Kristofer Henderson
#
# MIT License:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
File: test_metadata_list.py
Author: Kris Henderson
"""

import unittest
import os
import json

from metadata_list import MetadataList

class TestMetadataList(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

        self.filename = 'unittest-metadataset-file.json'
        self.metadata_list = None
        self.count = 2000

    def setUp(self):
        with open(self.filename, 'w') as file:
            data = {'files': []}
            for i in range(0, self.count):
                data['files'].append('file{:04}.json'.format(i))
            file.write(json.dumps(data, indent=4))

        self.metadata_list = MetadataList(self.filename)

    def tearDown(self):
        os.remove(self.filename)

    def test_peek_two_commit(self):
        self.assertEqual('file0000.json', self.metadata_list.peek_next_file())
        self.assertEqual('file0001.json', self.metadata_list.peek_next_file())
        self.metadata_list.commit()
        self.assertEqual('file0002.json', self.metadata_list.peek_next_file())
        self.assertEqual('file0003.json', self.metadata_list.peek_next_file())

    def test_peek_two_revert(self):
        self.assertEqual('file0000.json', self.metadata_list.peek_next_file())
        self.assertEqual('file0001.json', self.metadata_list.peek_next_file())
        self.metadata_list.revert()
        self.assertEqual('file0000.json', self.metadata_list.peek_next_file())
        self.assertEqual('file0001.json', self.metadata_list.peek_next_file())

    def test_in_memory(self):
        for i in range(0, self.count):
            self.assertEqual(self.count-i, self.metadata_list.get_remaining())
            fname = self.metadata_list.peek_next_file()
            self.assertEqual('file{:04}.json'.format(i), fname)
            self.metadata_list.commit()

    def test_with_reopen(self):
        for i in range(0, self.count):
            list2 = MetadataList(self.filename)
            self.assertEqual(self.count-i, list2.get_remaining())
            fname = list2.peek_next_file()
            self.assertEqual('file{:04}.json'.format(i), fname)
            self.metadata_list.peek_next_file()
            self.metadata_list.commit()

    def test_pop_and_reinit(self):
        for i in range(0, self.count):
            self.assertEqual(self.count-i, self.metadata_list.get_remaining())
            fname = self.metadata_list.peek_next_file()
            self.metadata_list.commit()
            self.assertEqual('file{:04}.json'.format(i), fname)
            self.metadata_list = MetadataList(self.filename)
