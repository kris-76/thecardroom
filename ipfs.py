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
File: ipfs.py
Author: Kris Henderson

Utility to upload files into IPFS and update a drop metametadata
"""

from typing import Dict
import argparse
import json
import logging
import os
import time
import requests

from database import Database
from cardano import Cardano
from nft import Nft
from wallet import Wallet
from wallet import WalletExternal
import command
import tcr
import words

logger = None

def setup_logging(network: str) -> None:
    # Setup logging INFO and higher goes to the console.  DEBUG and higher goes to file
    global logger

    logger = logging.getLogger(network)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    console_handler.setFormatter(console_format)

    file_handler = logging.FileHandler('log/{}_payments_{}.log'.format(network, round(time.time())))
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger_names = ['nft', 'cardano', 'command', 'database', 'tcr']
    for logger_name in logger_names:
        other_logger = logging.getLogger(logger_name)
        other_logger.setLevel(logging.DEBUG)
        other_logger.addHandler(console_handler)
        other_logger.addHandler(file_handler)

def set_metametadata(network: str, drop_name: str, metametadata: Dict) -> None:
    metametadata_file = 'nft/{}/{}/{}_metametadata.json'.format(network, drop_name, drop_name)
    with open(metametadata_file, 'w') as file:
        file.write(json.dumps(metametadata, indent=4))
    logger.info('Saved MetaMetaData: {}'.format(metametadata_file))

def get_metametadata(network: str, drop_name: str) -> Dict:
    series_metametadata = {}
    metametadata_file = 'nft/{}/{}/{}_metametadata.json'.format(network, drop_name, drop_name)
    logger.info('Open MetaMetaData: {}'.format(metametadata_file))
    with open(metametadata_file, 'r') as file:
        series_metametadata = json.load(file)
        if drop_name != series_metametadata['drop-name']:
            raise Exception('Unexpected Drop Name: {} vs {}'.format(drop_name, series_metametadata['drop-name']))
    return series_metametadata

def ipfs_upload(projectid: str, filename: str) -> str:
    headers = {'project_id': projectid}
    files = {'file': (os.path.basename(filename), open(filename, 'rb'))}

    logger.info('Uploading: {}'.format(filename))
    # Thank you!!  https://curl.trillworks.com/#python
    response = requests.post('https://ipfs.blockfrost.io/api/v0/ipfs/add',
                             headers=headers,
                             files=files)

    if response.status_code != 200:
        logger.error('Upload Status Code: {}'.format(response.status_code()))
        raise Exception('Upload Status Code: {}'.format(response.status_code()))

    upload_json = response.json()
    return upload_json['ipfs_hash']

def ipfs_pin(projectid: str, ipfs_hash: str) -> str:
    headers = {'project_id': projectid}

    logger.info('Pinning: {}'.format(ipfs_hash))

    # Thank you!!  https://curl.trillworks.com/#python
    response = requests.post('https://ipfs.blockfrost.io/api/v0/ipfs/pin/add/{}'.format(ipfs_hash),
                             headers=headers)
    if response.status_code != 200:
        logger.error('Pin Status Code: {}'.format(response.status_code()))
        raise Exception('Pin Status Code: {}'.format(response.status_code()))

    pin_json = response.json()
    if pin_json['state'] != 'queued' and pin_json['state'] != 'pinned':
        logger.error('PIN Unexpected State: {}'.format(pin_json['state']))
        raise Exception('PIN Unexpected State: {}'.format(pin_json['state']))

    if pin_json['ipfs_hash'] != ipfs_hash:
        logger.error('WUT?  {} != {}'.format(pin_json['ipfs_hash'], ipfs_hash))
        raise Exception('WUT?  {} != {}'.format(pin_json['ipfs_hash'], ipfs_hash))

    return pin_json['state']

def main():
    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--projectid', required=True,
                                       action='store',
                                       metavar='ID',
                                       help='API key from blockfrost')
    parser.add_argument('--network',   required=False,
                                       action='store',
                                       default='',
                                       metavar='NAME',
                                       help='Which network to use, [mainnet | testnet]')
    parser.add_argument('--drop',      required=False,
                                       action='store',
                                       default='',
                                       metavar='NAME',
                                       help='The name of the NFT drop.')
    parser.add_argument('--file',      required=False,
                                       action='store',
                                       metavar='NAME',
                                       help='Filename to upload and pin')

    args = parser.parse_args()

    projectid = args.projectid
    network = args.network
    drop_name = args.drop
    filename = args.file

    setup_logging(network)

    logger.info('{} IPFS Uploader / Metadata Generator'.format(network.upper()))
    logger.info('Copyright 2021 Kristofer Henderson & thecardroom.io')
    print('network = _{}_'.format(network))
    print('   drop = _{}_'.format(drop_name))
    if filename == None and (len(network) == 0 or len(drop_name) == 0):
        logger.error('Invalid parameters.  Must give --network and --drop')
        raise Exception('Invalid parameters.  Must give --network and --drop')

    if filename != None and (len(network) > 0 or len(drop_name) > 0):
        logger.error('Invalid parameters.  With --file, Do not set --network and --drop')
        raise Exception('Invalid parameters.  With --file, Do not set --network and --drop')

    if filename == None:
        # Upload and update content in a drop metametadata file
        if not network in command.networks:
            logger.error('Invalid Network: {}'.format(network))
            raise Exception('Invalid Network: {}'.format(network))

        logger.info('Network: {}'.format(network))
        logger.info('Drop: {}'.format(drop_name))

        metametadata = get_metametadata(network, drop_name)
        for card in metametadata['cards']:
            nftfilename = './nft/{}/{}/{}'.format(network, drop_name, card['local_source'])
            ipfs_hash = ipfs_upload(projectid, nftfilename)
            pin_state = ipfs_pin(projectid, ipfs_hash)
            logger.info('PIN State: {}'.format(pin_state))
            logger.info('   Verify: http://ipfs.blockfrost.dev/ipfs/{}'.format(ipfs_hash))
            logger.info('')
            card['image'] = 'ipfs://{}'.format(ipfs_hash)

        set_metametadata(network, drop_name, metametadata)
    else:
        # Just upload and pin the specified file
        logger.info('File: {}'.format(filename))
        ipfs_hash = ipfs_upload(projectid, filename)
        pin_state = ipfs_pin(projectid, ipfs_hash)
        logger.info('PIN State: {}'.format(pin_state))
        logger.info('   Verify: http://ipfs.blockfrost.dev/ipfs/{}'.format(ipfs_hash))
        logger.info('')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
