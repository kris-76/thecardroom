#
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

import json

import argparse

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--file', required=True,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='File to beautify')

    args = parser.parse_args()
    file_name = args.file

    object = None
    with open(file_name, 'r') as file:
        object = json.load(file)

    if object != None:
        with open(file_name, 'w') as file:
            file.write(json.dumps(object, indent=4))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
