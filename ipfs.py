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
import requests
import command
import nftmint

logger = None

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

def get_metadataset(network: str, drop_name: str) -> Dict:
    metadataset = {}
    metadataset_file = 'nft/{}/{}/{}.json'.format(network, drop_name, drop_name)
    logger.info('Open Metadata Set: {}'.format(metadataset_file))
    with open(metadataset_file, 'r') as file:
        metadataset = json.load(file)
    return metadataset

def ipfs_upload(projectid: str, projectsecret: str, filename: str) -> str:
    files = {'file': (os.path.basename(filename), open(filename, 'rb'))}

    logger.info('Uploading: {}'.format(filename))
    # Thank you!!  https://curl.trillworks.com/#python
    response = requests.post('https://ipfs.infura.io:5001/api/v0/add?pin=false',
                             files=files,
                             auth=(projectid, projectsecret))

    if response.status_code != 200:
        logger.error('Upload Status Code: {}'.format(response.status_code()))
        raise Exception('Upload Status Code: {}'.format(response.status_code()))

    upload_json = response.json()
    return upload_json['Hash']

def ipfs_pin(projectid: str, projectsecret: str, ipfs_hash: str) -> str:
    logger.info('Pinning: {}'.format(ipfs_hash))
    # Thank you!!  https://curl.trillworks.com/#python
    params = {('arg', ipfs_hash)}
    response = requests.post('https://ipfs.infura.io:5001/api/v0/pin/add',
                             params=params,
                             auth=(projectid, projectsecret))

    if response.status_code != 200:
        logger.error('Pin Status Code: {}'.format(response.status_code()))
        raise Exception('Pin Status Code: {}'.format(response.status_code()))

    pin_json = response.json()
    if ipfs_hash not in pin_json['Pins']:
        logger.error('WUT?  {} != {}'.format(pin_json['Pins'], ipfs_hash))
        raise Exception('WUT?  {} != {}'.format(pin_json['Pins'], ipfs_hash))

    return True

def main():
    global logger

    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--projectid', required=True,
                                       action='store',
                                       metavar='ID',
                                       help='Project ID from infura.io')
    parser.add_argument('--projectsecret', required=True,
                                           action='store',
                                           metavar='ID',
                                           help='Project secret from infura.io')
    parser.add_argument('--network', required=False,
                                     action='store',
                                     default='',
                                     metavar='NAME',
                                     help='Which network to use (to find drop file), [mainnet | testnet]')
    parser.add_argument('--drop',    required=False,
                                     action='store',
                                     default='',
                                     metavar='NAME',
                                     help='The name of the NFT drop.')
    parser.add_argument('--file',    required=False,
                                     action='store',
                                     default=None,
                                     metavar='NAME',
                                     help='Filename to upload and pin')

    args = parser.parse_args()

    projectid = args.projectid
    projectsecret = args.projectsecret
    network = args.network
    drop_name = args.drop
    filename = args.file

    nftmint.setup_logging(network, 'ipfs')
    logger = logging.getLogger(network)

    logger.info('{} IPFS Uploader / Metadata Generator'.format(network.upper()))
    logger.info('Copyright 2021 Kristofer Henderson & thecardroom.io')

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
        if 'cards' in metametadata and len(metametadata['cards']) > 0:
            for card in metametadata['cards']:
                nftfilename = './nft/{}/{}/{}'.format(network, drop_name, card['local_source'])
                ipfs_hash = ipfs_upload(projectid, projectsecret, nftfilename)
                pin_state = ipfs_pin(projectid, projectsecret, ipfs_hash)
                logger.info('PIN State: {}'.format(pin_state))
                logger.info('   Verify: http://ipfs.io/ipfs/{}'.format(ipfs_hash))
                logger.info('')
                card['image'] = 'ipfs://{}'.format(ipfs_hash)
            set_metametadata(network, drop_name, metametadata)
        elif 'layer-sets' in metametadata and len(metametadata['layer-sets']) > 0:
            metadataset = get_metadataset(network, drop_name)
            for filename in metadataset['files']:
                nftmetadata = {}
                logger.info("Open NFT Metadata: {}".format(filename))
                with open(filename, 'r') as mdfile:
                    nftmetadata = json.load(mdfile)

                policy_id = list(nftmetadata['721'].keys())[0]
                token_name = list(nftmetadata['721'][policy_id].keys())[0]
                if not nftmetadata['721'][policy_id][token_name]['image'].startswith('ipfs://'):
                    logger.info('Upload: {} / {}'.format(nftmetadata['721'][policy_id][token_name]['image'], filename))
                    ipfs_hash = ipfs_upload(projectid, projectsecret, nftmetadata['721'][policy_id][token_name]['image'])
                    pin_state = ipfs_pin(projectid, projectsecret, ipfs_hash)
                    logger.info('PIN State: {}'.format(pin_state))

                    nftmetadata['721'][policy_id][token_name]['image'] = 'ipfs://{}'.format(ipfs_hash)
                    with open(filename, 'w') as f:
                        f.write(json.dumps(nftmetadata, indent=4))
                        logger.info('Saved MetaMetaData: {}'.format(filename))

                    logger.info('   Verify: http://ipfs.io/ipfs/{}'.format(ipfs_hash))
                    logger.info('')
    else:
        # Just upload and pin the specified file
        logger.info('File: {}'.format(filename))
        ipfs_hash = ipfs_upload(projectid, projectsecret, filename)
        pin_state = ipfs_pin(projectid, projectsecret, ipfs_hash)
        logger.info('PIN State: {}'.format(pin_state))
        logger.info('   Verify: http://ipfs.io/ipfs/{}'.format(ipfs_hash))
        logger.info('')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
