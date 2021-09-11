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
File: words.py
Author: Kris Henderson
"""

from typing import List
import random

def generate_word_list(filename: str, count: int) -> List[str]:
    """
    Generate a list of unique words in random order.

    @param filename Test file to open
    @param count The number of unique words to return.

    Open the file and split it into words.  Then convert it into a dictionary
    and back to a list to get the unique words only.  Finally, slice the list
    up to count items.  May return a list shorter than count if there are not
    enough unique words in the input text file.

    @return List of strings
    """

    words = []

    with open(filename, 'r') as f:
       data = f.read()
       data = data.lower()
       data = data.replace(',', ' ')
       data = data.replace('.', ' ')
       data = data.replace(';', ' ')
       data = data.replace('\r', ' ')
       data = data.replace('\n', ' ')
       data = data.replace('"', ' ')
       data = data.replace('“', ' ')
       data = data.replace('”', ' ')
       words = data.split()

       # Make all the words unique
       words = list(dict.fromkeys(words))

    words = words[0:count]
    random.shuffle(words)
    return words
