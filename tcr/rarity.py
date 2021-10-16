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
    args = parser.parse_args()
    directory = args.directory

    properties = {}

    filenames= os.listdir(directory)
    filenames.sort()
    for filename in filenames:
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and f.endswith('.json'):
            with open(f, 'r') as file:
                md = json.load(file)
                erc721 = md['721']
                policy = erc721[list(erc721.keys())[0]]
                token = policy[list(policy.keys())[0]]

                # TODO, search feature would be nice
                #character = 'x'
                #mutation = 'x'
                #if token['character'] == character and token['mutation'] == mutation:
                #    print('{} {}: {}'.format(character, mutation, filename))

                token['saliva+teeth'] = token['saliva'] + '+' + token['teeth']
                token['saliva+scene'] = token['saliva'] + '+' + token['scene']
                token['teeth+scene'] = token['teeth'] + '+' + token['scene']
                token['saliva+teeth+scene'] = token['saliva'] + '+' + token['teeth'] + '+' + token['scene']
                token['flavor+potency'] = token['flavor'] + '+' + token['potency']

                for key in token:
                    if not key in properties:
                        properties[key] = {}

                    value = token[key]
                    if type(value) is list:
                        for subvalue in value:
                            if not subvalue in properties[key]:
                                properties[key][subvalue] = 1
                            else:
                                properties[key][subvalue] += 1
                    else:
                        if not value in properties[key]:
                            properties[key][value] = 1
                        else:
                            properties[key][value] += 1

    for name in properties['name']:
        if properties['name'][name] != 1:
            print("ERROR, invalid name count: {}".format(properties['name'][name]))

    for image in properties['image']:
        if properties['image'][image] != 1:
            print("ERROR, invalid image count: {}".format(properties['image'][image]))

    for id in properties['id']:
        if properties['id'][id] != 1:
            print("ERROR, invalid id count: {}".format(properties['id'][id]))

    total = len(properties['name'])
'''
    for key in properties:
        if key == 'name' or key == 'image' or key == 'publisher' or key == 'description' or key == 'artist' or key == 'id':
            continue

        values = list(properties[key].keys())
        values.sort(reverse=True, key=lambda item: properties[key][item])
        print('{}'.format(key))
        i = 1
        for value in values:
            print('\t{}. {:30} = {:5}/{} = {}%'.format(i, value, properties[key][value], total, (properties[key][value]*100)/total))
            i += 1

        print('')
'''


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
        print(e.format_exc())
