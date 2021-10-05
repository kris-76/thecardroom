#
# Copyright 2021 Kristofer Henderson
#
# This file not licensed for use.
#

from typing import List, Set, Dict
from wallet import Wallet
from wallet import WalletExternal
from cardano import Cardano
from nft import Nft
import tcr
from database import Database
import random
import json
import os
import logging
import argparse
import nftmint
import command
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

    if not network in command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    nftmint.setup_logging(network, 'buybot')
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
    dst_wallet = Wallet(dst_name, cardano.get_network())

    cardano.dump_utxos_sorted(database, src_wallet)
    if amount >= 0:
        send_payment = True
        while send_payment:
            if amount > 0:
                tx_id = tcr.transfer_ada(cardano, src_wallet, amount, dst_wallet)
            elif all == True:
                tx_id = tcr.transfer_all_assets(cardano, src_wallet, dst_wallet)
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
        tx_id = tcr.transfer_nft(cardano, src_wallet, {nft: 1}, dst_wallet)
        while not cardano.contains_txhash(dst_wallet, tx_id):
            time.sleep(5)

if __name__ == '__main__':
    main()
