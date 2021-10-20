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

from typing import List, Set, Dict
from tcr.wallet import Wallet
from tcr.wallet import WalletExternal
from tcr.cardano import Cardano
from tcr.nft import Nft
import tcr.tcr
from tcr.database import Database
import json
import os
import logging
import argparse
import tcr.nftmint
import tcr.command
import time

def main():
    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network', required=True,
                                     action='store',
                                     type=str,
                                     metavar='NAME',
                                     help='Which network to use, [mainnet | testnet]')

    parser.add_argument('--src', required=True,
                                  action='store',
                                  type=str,
                                  metavar='NAME',
                                  default=None,
                                  help='Wallet name to send from.')

    parser.add_argument('--dst', required=True,
                                  action='store',
                                  type=str,
                                  metavar='NAME',
                                  default=None,
                                  help='Wallet name to send to.')

    parser.add_argument('--amount', required=False,
                                    action='store',
                                    type=int,
                                    metavar='NAME',
                                    default=0,
                                    help='Amount of lovelace to send')

    parser.add_argument('--all', required=False,
                                 action='store_true',
                                 default=False,
                                 help='Confirm to send all')

    parser.add_argument('--repeat', required=False,
                                    action='store_true',
                                    default=False,
                                    help='Continuously send specified amount')

    parser.add_argument('--nft', required=False,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    default=None,
                                    help='Full name of NFT to send')
    args = parser.parse_args()
    network = args.network
    src_name = args.src
    dst_name = args.dst
    amount = args.amount
    all = args.all
    nft = args.nft
    repeat = args.repeat

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'buybot')
    logger = logging.getLogger(network)

    # Setup connection to cardano node, cardano wallet, and cardano db sync
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))
    logger.info('{} Buy Bot'.format(network.upper()))
    logger.info('Copyright 2021 Kristofer Henderson & thecardroom.io')
    logger.info('Network: {}'.format(network))

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']

    database = Database('{}.ini'.format(network))
    database.open()
    meta = database.query_chain_metadata()
    db_size = database.query_database_size()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.info('Database Chain Metadata: {} / {}'.format(meta[1], meta[2]))
    logger.info('Database Size: {}'.format(db_size))
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('Sync Progress: {}'.format(sync_progress))

    src_wallet = Wallet(src_name, cardano.get_network())

    if dst_name.startswith('addr'):
        dst_wallet = WalletExternal('External', cardano.get_network(), dst_name)
    else:
        dst_wallet = Wallet(dst_name, cardano.get_network())

    cardano.dump_utxos_sorted(database, src_wallet)
    if amount >= 0:
        send_payment = True
        while send_payment:
            if amount > 0:
                tx_id = tcr.tcr.transfer_ada(cardano, src_wallet, amount, dst_wallet)
            elif all == True:
                tx_id = tcr.tcr.transfer_all_assets(cardano, src_wallet, dst_wallet)
            else:
                logger.error("Nothing to Send")
                break

            if tx_id == None:
                repeat = False
            else:
                while not cardano.contains_txhash(dst_wallet, tx_id):
                    time.sleep(5)

            send_payment = repeat
    elif nft != None:
        tx_id = tcr.tcr.transfer_nft(cardano, src_wallet, {nft: 1}, dst_wallet)
        while not cardano.contains_txhash(dst_wallet, tx_id):
            time.sleep(5)

if __name__ == '__main__':
    main()
