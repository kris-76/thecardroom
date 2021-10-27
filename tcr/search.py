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

import os
import argparse
import json

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--directory', required=True,
                                       action='store',
                                       type=str,
                                       metavar='NAME',
                                       help='')
    parser.add_argument('--filter', required=True,
                                    action='store',
                                    type=str,
                                    metavar='PATTERN',
                                    help='')
    args = parser.parse_args()
    directory = args.directory
    filter = args.filter

    properties = {}
    for pair in filter.split(','):
        properties[pair.split('=')[0]] = pair.split('=')[1]

    filenames= os.listdir(directory)
    filenames.sort()
    count = 1
    print('Search: {}'.format(properties))
    for filename in filenames:
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and f.endswith('.json'):
            with open(f, 'r') as file:
                md = json.load(file)
                erc721 = md['721']
                policy = erc721[list(erc721.keys())[0]]
                token = policy[list(policy.keys())[0]]


                match = True
                for key in properties:

                    if type(token[key]) is list:
                        if properties[key] not in token[key]:
                            match = False
                            break
                    else:
                        if properties[key] != token[key]:
                            match = False
                            break

                if match:
                    print('\t{}. {}'.format(count, f))
                    count += 1

    print('')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
        print(e.format_exc())
