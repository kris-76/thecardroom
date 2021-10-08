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
File: metadata_list.py
Author: Kris Henderson
"""

import logging
import json

logger = logging.getLogger('metadata-list')

class MetadataList:
    def __init__(self, metadata_set_file):
        self.metadata_set_file = metadata_set_file
        self.metadata_list = {}
        self.peek_index = 0

        with open(self.metadata_set_file, 'r') as file:
            logger.info('MetadataList, Opened: {}'.format(metadata_set_file))

            self.metadata_list = json.loads(file.read())
            if self.metadata_list == None:
                logger.error('MetadataList, Series Metadata Set is None')
                raise Exception('MetadataList, Series Metadata Set is None')

            if self.metadata_list['files'] == None:
                logger.error('MetadataList, Series Metadata Set missing \"files\"')
                raise Exception('MetadataList, Series Metadata Set missing \"files\"')

    def get_remaining(self) -> int:
        return len(self.metadata_list['files']) - self.peek_index

    def peek_next_file(self) -> str:
        filename = self.metadata_list['files'][self.peek_index]
        self.peek_index += 1
        return filename

    def revert(self) -> None:
        self.peek_index = 0

    def commit(self) -> None:
        while self.peek_index > 0:
            self.metadata_list['files'].pop(0)
            self.peek_index -= 1

        with open(self.metadata_set_file, 'w') as file:
            file.write(json.dumps(self.metadata_list, indent=4))
