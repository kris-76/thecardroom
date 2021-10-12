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
from tcr.command import Command
import logging
import hashlib
import numpy

from PIL import Image

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
        layer_sets = metametadata['layer-sets']
        layer_set_weight = 0
        dir = os.path.dirname(os.path.abspath(metametadata['self']))
        for layer_set_item in layer_sets:
            with open(os.path.join(dir, layer_set_item['file']), 'r') as ls_file:
                logger.info("Opening Layer Set: {}".format(layer_set_item['file']))
                layer_set = json.load(ls_file)

            layer_set_weight += layer_set_item['weight']
            combos = 1
            for layer in layer_set['layers']:
                logger.info("{} - {} = {}".format(layer_set_item['file'], layer['name'], len(layer['images'])))
                combos = combos * len(layer['images'])
                image_weight_total = 0
                for image in layer['images']:
                    logger.debug('{} + {} = {}'.format(image_weight_total, image['weight'], image_weight_total+image['weight']))
                    image_weight_total += image['weight']
                    if image['image'] != None:
                        dir = os.path.dirname(os.path.abspath(metametadata['self']))
                        image_path = os.path.join(dir, image['image'])
                        im = Image.open(image_path)
                        (width, height) = im.size
                        if width != layer['width'] or height != layer['height']:
                            logger.error('{} != {} x {}'.format(image['image'], layer['width'], layer['height']))

                if abs(100 - image_weight_total) > 0.0001:
                    logger.error('{}, {} Image weight {} != 100'.format(layer_set_item['file'], layer['name'], image_weight_total))
                    raise Exception('{}, {} Image weight {} != 100'.format(layer_set_item['file'], layer['name'], image_weight_total))

            logger.info('{} = {}'.format(layer_set_item['file'], combos))
            total += combos

        if layer_set_weight != 100:
            logger.error('Layer Set weight {} != 100'.format(layer_set_weight))
            raise Exception('Layer Set weight {} != 100'.format(layer_set_weight))

        return total

    @staticmethod
    def calc_sha256(filepath) :
        BLOCKSIZE = 65536
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        return hasher.hexdigest()

    @staticmethod
    def create_series_metadata_set(network: str,
                                   policy_id: str,
                                   metametadata: Dict,
                                   codewords: List[str],
                                   rng: numpy.random.RandomState) -> List[str]:
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
                num = rng.randint(0, total)
                for l in card_lists:
                    if num > len(l):
                        num -= len(l)
                    elif len(l) > 0:
                        item = l.pop(0)
                        fnames.append(item)
                        break
                total -=1
        else:
            image_hashes = {}
            image_names = {}

            total_combinations = Nft.calculate_total_combinations(metametadata)
            logger.info('Total Combinations: {} images, Layer Sets: {} sets'.format(total_combinations, len(metametadata['layer-sets'])))
            logger.info('NFTs to generate: {}'.format(metametadata['total']))

            total_to_generate = metametadata['total']
            fnames = []

            frequencies = [0] * 101

            while len(fnames) < total_to_generate:
                images = []
                metadata = {}
                properties = {}

                logger.info('Created: {}'.format(len(fnames)))
                # 1.  Randomly choose a layer-set according to weight of all
                # layer sets.  The weight must add to 100
                sum = 0
                num = rng.random() * 100
                frequencies[round(num)] += 1
                layer_sets = metametadata['layer-sets']
                layer_set_obj = None
                for layer_set_item in layer_sets:
                    if num <= sum + layer_set_item['weight']:
                        dir = os.path.dirname(os.path.abspath(metametadata['self']))
                        with open(os.path.join(dir, layer_set_item['file']), 'r') as ls_file:
                            layer_set_obj = json.load(ls_file)
                        break
                    sum += layer_set_item['weight']

                if layer_set_obj == None:
                    logger.error('Unexpected layer_set_obj == None')
                    raise Exception('Unexpected layer_set_obj == None')

                card_number = len(fnames) + 1
                result_name = 'nft/{}/{}/nft_img/{:05}_'.format(network, drop_name, card_number)
                image_name = '{}_'.format(layer_set_obj['name'])

                # 2. Now iterate each layer in the chosen layer set and randomly
                # select an image from it
                for layer in layer_set_obj['layers']:
                    sum = 0
                    num = rng.random() * 100
                    frequencies[round(num)] += 1
                    img_obj = None
                    img_idx = 0
                    for image in layer['images']:
                        if num <= sum + image['weight']:
                            img_obj = image
                            break
                        sum += image['weight']
                        img_idx += 1

                    if img_obj == None:
                        logger.error('Unexpected image_obj == None')
                        raise Exception('Unexpected image_obj == None')

                    image_name = image_name + '_{}'.format(img_idx)
                    if img_obj['image'] != None:
                        images.append(img_obj)

                    # Add any metadata / properties associated with the image layer.  I suppose
                    # later layers could override some properties from previous layers
                    if 'properties' in img_obj:
                        layer_properties = img_obj['properties']
                        for k in layer_properties:
                            properties[k] = layer_properties[k]

                # Construct the command to merge image layers
                if image_name in image_names:
                    logger.info('Already exists, try again: {}'.format(image_name))
                    continue

                image_names[image_name] = True
                result_name = result_name + image_name + '.png'
                logger.info('Create: {}'.format(result_name))
                command = ['convert']
                for image in images:
                    if image['offset-x'] >= 0:
                        geometry = '+{}'.format(image['offset-x'])
                    else:
                        geometry = '{}'.format(image['offset-x'])

                    if image['offset-y'] >= 0:
                        geometry += '+{}'.format(image['offset-y'])
                    else:
                        geometry += '{}'.format(image['offset-y'])

                    if len(command) == 1:
                        command.extend(['nft/{}/{}/{}'.format(network, drop_name, image['image']), '-geometry', geometry])
                    else:
                        command.extend(['nft/{}/{}/{}'.format(network, drop_name, image['image']), '-geometry', geometry, '-composite'])

                # Create the file
                command.append(result_name)
                Command.run_generic(command)

                # Make sure it got created
                if not os.path.isfile(result_name):
                    logger.error('File is missing: {}'.format(result_name))
                    raise Exception('File is missing: {}'.format(result_name))

                # Make sure the generated file is unique
                logger.info('Verify Unique: {}'.format(result_name))
                hash = Nft.calc_sha256(result_name)
                if hash in image_hashes:
                    logger.error('Found Duplicate NFT Image: {} exists at {} for {}'.format(image_hashes[hash], hash, result_name))
                    raise Exception('Found Duplicate NFT Image: {} exists at {} for {}'.format(image_hashes[hash], hash, result_name))
                image_hashes[hash] = result_name

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
            # should already be sorted....
            # fnames.sort()
            for i in range(0, len(frequencies)):
                logger.info('frequencies[{}] = {}'.format(i, frequencies[i]))

        return fnames
