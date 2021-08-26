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

import json

class Nft:
    @staticmethod
    def create_metadata(network, policy_id, token_name, nft_name, image, description, properties):
        """
        Write JSON metadata according to the Cardano NFT metadata format proposal.

        Test the output at https://pool.pm/test/metadata
        """
        
        metadata_file = 'nft/{}/{}_metadata.json'.format(network, token_name)
        metadata = {}
        metadata["721"] = {}
        metadata["721"][policy_id] = {}
        metadata["721"][policy_id][token_name] = {}
        metadata["721"][policy_id][token_name]["name"] = nft_name
        metadata["721"][policy_id][token_name]["image"] = image
        metadata["721"][policy_id][token_name]["description"] = description

        for key in properties:
            metadata["721"][policy_id][token_name][key] = properties[key]

        with open(metadata_file, 'w') as file:
            file.write(json.dumps(metadata, indent=4))
