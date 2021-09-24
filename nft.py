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
File: nft.py
Author: Kris Henderson
"""

from typing import Dict, List
import json
import os
import time
import random
from command import Command
import logging

logger = logging.getLogger('nft')

class Nft:
    @staticmethod
    def parse_metadata_file(metadata_file: str) -> Dict:
        """
        Parse a NFT metadata file.  The metadata file can define a single asset
        or multiple assets.

        The returned dictionary will look like this:
        {
            'policy-id': 'the-policy-id,
            'token-names': ['tname1', 'tname2', ..., 'tnamen'],
            'properties': {
                'tname1': {...},
                'tname2': {...},
                'tnamen': {...}
            }
        }

        """
        metadata = {}

        with open(metadata_file, 'r') as file:
            raw_md = json.load(file)
            policy_id = list(raw_md['721'].keys())[0]
            token_names = list(raw_md['721'][policy_id].keys())
            metadata['policy-id'] = policy_id
            metadata['token-names'] = token_names
            metadata['properties'] = {}
            for token_name in token_names:
                metadata['properties'][token_name] = raw_md['721'][policy_id][token_name]

        return metadata

    @staticmethod
    def merge_metadata_files(policy_id: str, nft_metadata_files: List[str]) -> str:
        directory = os.path.dirname(nft_metadata_files[0])
        merged_file = os.path.join(directory, 'nft_merged_metadata_{}.json'.format(round(time.time())))

        nft_merged_metadata = {}
        nft_merged_metadata['721'] = {}
        nft_merged_metadata['721'][policy_id] = {}
        for fname in nft_metadata_files:
            nftmd = Nft.parse_metadata_file(fname)
            token_name = nftmd['token-names'][0]
            nft_merged_metadata['721'][policy_id][token_name] = nftmd['properties'][token_name]

        with open(merged_file, 'w') as file:
            file.write(json.dumps(nft_merged_metadata, indent=4))

        return merged_file

    @staticmethod
    def create_metadata(network: str,
                        policy_id: str,
                        drop_name: str,
                        token_name: str,
                        nft_name: str,
                        mdin: Dict) -> str:
        """
        Write JSON metadata according to the Cardano NFT metadata format proposal.

        Test the output at https://pool.pm/test/metadata
        """

        md_dir = 'nft/{}/{}/nft_metadata'.format(network, drop_name)
        metadata_file = '{}/{}.json'.format(md_dir, token_name)

        if not os.path.exists(md_dir):
            os.makedirs(md_dir)

        metadata = {}
        metadata["721"] = {}
        metadata["721"][policy_id] = {}
        metadata["721"][policy_id][token_name] = {}
        metadata["721"][policy_id][token_name]["name"] = nft_name
        if 'image' in mdin:
            metadata["721"][policy_id][token_name]["image"] = mdin['image']
        if 'description' in mdin:
            metadata["721"][policy_id][token_name]["description"] = mdin['description']

        for key in mdin['properties']:
            metadata["721"][policy_id][token_name][key] = mdin['properties'][key]

        with open(metadata_file, 'w') as file:
            file.write(json.dumps(metadata, indent=4))

        return metadata_file

    @staticmethod
    def create_card_metadata_set(network: str,
                                 policy_id: str,
                                 series_name: str,
                                 base_nft_id: int,
                                 token_name: str,
                                 nft_name: str,
                                 metadata: Dict,
                                 codewords: List[str]) -> List[str]:
        count = metadata['count']
        fnames = []
        for i in range(0, count):
            if 'id' in metadata['properties']:
                metadata['properties']['id'] = base_nft_id + i

            if 'code' in metadata['properties']:
                metadata['properties']['code'] = random.randint(0, 0xFFFFFFFF)

            if 'word' in metadata['properties']:
                metadata['properties']['word'] = codewords.pop()

            fname = Nft.create_metadata(network,
                                        policy_id,
                                        series_name,
                                        token_name.format(i+1),
                                        nft_name.format(i+1),
                                        metadata)
            fnames.append(fname)
        return fnames

    @staticmethod
    def calculate_total_combinations(metametadata: Dict):
        total = 0
        layer_set_names = metametadata['layer-sets']
        for layer_set_name in layer_set_names:
            layer_set = metametadata[layer_set_name]
            layer_set_combinations = 1
            for layer in layer_set:
                layer_set_combinations *= len(layer['images'])

            logger.info('Layer {} = {} combinations'.format(layer_set_name, layer_set_combinations))
            total += layer_set_combinations

        return total

    @staticmethod
    def create_series_metadata_set(network: str,
                                   policy_id: str,
                                   metametadata: Dict,
                                   codewords: List[str]) -> List[str]:
        series = metametadata['series']
        drop_name = metametadata['drop-name']
        init_nft_id = metametadata['init-nft-id']
        base_token_name = metametadata['token-name']
        base_nft_name = metametadata['nft-name']

        if "cards" in metametadata:
            card_lists = []
            total = 0
            for card in metametadata['cards']:
                token_name = base_token_name.format(series, card['id'], '{:03}')
                nft_name = base_nft_name.format(series, card['id'], '{}', card['count'])
                files = Nft.create_card_metadata_set(network,
                                                     policy_id,
                                                     drop_name,
                                                     init_nft_id,
                                                     token_name,
                                                     nft_name,
                                                     card,
                                                     codewords)
                card_lists.append(files)
                total += card['count']

                init_nft_id += card['count']

            fnames = []
            while total > 0:
                num = random.randint(0, total-1)
                for l in card_lists:
                    if num > len(l):
                        num -= len(l)
                    elif len(l) > 0:
                        item = l.pop(0)
                        fnames.append(item)
                        break
                total -=1
        else:
            total_combinations = Nft.calculate_total_combinations(metametadata)
            logger.info('Generate {} images across {} sets'.format(total_combinations, len(metametadata['layer-sets'])))

            # assign card numbers randomly
            card_numbers = []
            for x in range(1, total_combinations+1):
                card_numbers.append(x)
            random.shuffle(card_numbers)

            layer_set_names = metametadata['layer-sets']
            fnames = []
            for layer_set_name in layer_set_names:
                layer_set = metametadata[layer_set_name]

                options = [0] * len(layer_set)
                done = False
                while not done:
                    images = []
                    card_number = card_numbers.pop(0)
                    result_name = 'nft/{}/{}/nft_img/{:05}_{}_'.format(network, drop_name, card_number, layer_set_name)
                    metadata = {}
                    properties = {}
                    for i in range(0, len(options)):
                        # Set a filename to identify the components that went into it
                        result_name = result_name + '_{}'.format(options[i])

                        # Save the image for merging
                        if layer_set[i]['images'][options[i]]['image'] != None:
                            images.append(layer_set[i]['images'][options[i]]['image'])

                        # Add any metadata / properties associated with the image layer.  I suppose
                        # later layers could override some properties from previous layers
                        if 'properties' in layer_set[i]['images'][options[i]]:
                            layer_properties = layer_set[i]['images'][options[i]]['properties']
                            for k in layer_properties:
                                properties[k] = layer_properties[k]

                    # Construct the command to merge image layers
                    result_name = result_name + '.png'
                    logger.info('Create: {}'.format(result_name))
                    command = ['convert', 'nft/{}/{}/{}'.format(network, drop_name, images.pop(0))]
                    for image in images:
                        command.extend(['nft/{}/{}/{}'.format(network, drop_name, image), '-composite'])

                    # Create the file
                    command.append(result_name)
                    Command.run_generic(command)

                    token_name = base_token_name.format(series, card_number, 1)
                    nft_name = base_nft_name.format(series, card_number, 1, 1)

                    metadata['image'] = result_name
                    if 'id' in properties:
                        properties['id'] = init_nft_id + card_number - 1
                    metadata['properties'] = properties
                    metadata_file = Nft.create_metadata(network,
                                                        policy_id,
                                                        drop_name,
                                                        token_name,
                                                        nft_name,
                                                        metadata)
                    fnames.append(metadata_file)

                    for i in range(0, len(options)):
                        options[i] += 1
                        if options[i] < len(layer_set[i]['images']):
                            break
                        else:
                            options[i] = 0

                    done = True
                    for idx in options:
                        if idx != 0:
                            done = False

            fnames.sort()

        if 'maximum' in metametadata:
            fnames = fnames[0: metametadata['maximum']]

        return fnames
