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
                        series_name: str,
                        token_name: str,
                        nft_name: str,
                        mdin: Dict) -> str:
        """
        Write JSON metadata according to the Cardano NFT metadata format proposal.

        Test the output at https://pool.pm/test/metadata
        """

        md_dir = 'nft/{}/{}'.format(network, series_name)
        metadata_file = '{}/{}_metadata.json'.format(md_dir, token_name)

        if not os.path.exists(md_dir):
            os.makedirs(md_dir)

        metadata = {}
        metadata["721"] = {}
        metadata["721"][policy_id] = {}
        metadata["721"][policy_id][token_name] = {}
        metadata["721"][policy_id][token_name]["name"] = nft_name
        metadata["721"][policy_id][token_name]["image"] = mdin['image']
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
                                 metadata: Dict) -> List[str]:
        count = metadata['count']
        fnames = []
        for i in range(0, count):
            metadata['properties']['id'] = base_nft_id + i
            fname = Nft.create_metadata(network, policy_id, series_name, token_name.format(i+1), nft_name.format(i+1), metadata)
            fnames.append(fname)
        return fnames

    @staticmethod
    def create_series_metadata_set(network: str,
                                   policy_id: str,
                                   metadata: Dict) -> List[str]:
        series = metadata['series']
        series_name = metadata['drop-name']
        init_nft_id = metadata['init-nft-id']
        base_token_name = metadata['token-name']
        base_nft_name = metadata['nft-name']

        fnames = []
        for card in metadata['cards']:
            token_name = base_token_name.format(series, card['id'], '{:03}')
            nft_name = base_nft_name.format(series, card['id'], '{}', card['count'])
            files = Nft.create_card_metadata_set(network, policy_id, series_name, init_nft_id, token_name, nft_name, card)

            init_nft_id += card['count']
            fnames.extend(files)

        return fnames
