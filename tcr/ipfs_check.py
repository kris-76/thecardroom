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

from typing import Dict
import argparse
import json
import logging
import os
import requests
import tcr.command
import tcr.nftmint
import traceback
import hashlib

"""
File: ipfs_check.py
Author: Kris Henderson

After files have been uploaded to IPFS with ipfs.py, this utility checks to make
sure each metadata file has been correctly updated as well as the file on IPFS
is able to be downloaded and matches the original
"""

logger = None

def calc_sha256(filepath: str) :
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def main():
    global logger

    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network',   required=True,
                                       action='store',
                                       metavar='network',
                                       help='<testnet | mainnet>')
    parser.add_argument('--directory', required=True,
                                       action='store',
                                       metavar='LOCATION',
                                       help='Directory containing metadata and images')

    args = parser.parse_args()
    directory = args.directory
    network = args.network

    tcr.nftmint.setup_logging(network, 'ipfs_check')
    logger = logging.getLogger(network)

    img_dir = os.path.join(directory, 'nft_img')
    md_dir = os.path.join(directory, 'nft_metadata')

    image_files = os.listdir(img_dir)
    metadata_files = os.listdir(md_dir)

    image_files.sort()
    metadata_files.sort()

    if len(image_files) != len(metadata_files):
        logger.error('Length not equal, {} != {}'.format(len(image_files), len(metadata_files)))

    for i in range(0, len(image_files)):
        with open(os.path.join(md_dir, metadata_files[i]), 'r') as file:
                md = json.load(file)
                erc721 = md['721']
                policy = erc721[list(erc721.keys())[0]]
                token = policy[list(policy.keys())[0]]

                image = token['image']
                cid = image[7:]

                logger.info('Verify: {}'.format(metadata_files[i]))
                download_url = 'http://ipfs.io/ipfs/{}'.format(cid)
                logger.info('Download: {}'.format(download_url))
                r = requests.get(download_url)
                hasher = hashlib.sha256()
                hasher.update(r.content)
                ipfs_hash = hasher.hexdigest()
                logger.info('Compare: {}'.format(image_files[i]))
                local_hash = calc_sha256(os.path.join(img_dir, image_files[i]))

                if local_hash != ipfs_hash:
                    logger.error('HASH Not Equal!!')
                    raise Exception('HASH Not Equal!!')




if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
