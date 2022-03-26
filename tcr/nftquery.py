#
# Copyright 2022 Kristofer Henderson
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

from tcr.wallet import Wallet
from tcr.wallet import WalletExternal
from tcr.cardano import Cardano
from tcr.database import Database
import logging
import argparse
import tcr.command
import tcr.nftmint
import traceback
import json

# Simple application to query db-sync for the metadata associated with the NFT
# in a mint transaction.  Note that it's possible for a NFT or token to have
# multiple mint transactions.  In case of multiples, the newest metadata is
# returned.
def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network', required=True,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='Which network to use, [mainnet | testnet]')
    parser.add_argument('--fingerprint',  required=True,
                                          action='store',
                                          type=str,
                                          default=None,
                                          metavar='NAME',
                                          help='Fingerprint of desired NFT')
    args = parser.parse_args()
    network = args.network
    fingerprint = args.fingerprint

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'nftquery')
    logger = logging.getLogger(network)

    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']

    database = Database('{}.ini'.format(network))
    database.open()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('Sync Progress: {}'.format(sync_progress))

    if fingerprint != None:
        (policy, metadata) = database.query_nft_metadata(fingerprint)
        logger.info(json.dumps(metadata, indent=4))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
