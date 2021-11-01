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

    parser.add_argument('--utxo', required=True,
                                  action='store',
                                  type=str,
                                  metavar='UTXO',
                                  default=None,
                                  help='UTXO to refund')

    args = parser.parse_args()
    network = args.network
    src_name = args.src
    utxo_string = args.utxo

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'refund')
    logger = logging.getLogger(network)

    # Setup connection to cardano node, cardano wallet, and cardano db sync
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))
    logger.info('{} Refund'.format(network.upper()))
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

    if not src_wallet.exists():
        logger.error("Source wallet missing: {}".format(src_wallet.get_name()))
        raise Exception("Source wallet missing: {}".format(src_wallet.get_name()))

    (utxos, lovelace) = cardano.query_utxos(src_wallet)

    utxo_obj = None
    for utxo in utxos:
        if utxo['tx-hash'] == utxo_string:
            utxo_obj = utxo
            break

    if utxo_obj == None:
        logger.error("UTXO not found: {}".format(utxo_string))
        raise Exception("UTXO not found: {}".format(utxo_string))

    inputs = database.query_utxo_inputs(utxo_string)
    if len(inputs) == 0:
        logger.warning('Refund Payment, No UTXO Inputs - Waiting for DB SYNC.  Skip for now.')
        return

    input_address = inputs[0]['address']
    logger.info('Refunding: {} = {}'.format(utxo_obj['tx-hash'], utxo_obj['amount']))
    logger.info('Destination: {}'.format(input_address))

    # There can be different addresses in the inputs but they should be from the
    # same wallet, Arbitrarily pick the first one.
    destination = WalletExternal('customer',
                                 cardano.get_network(),
                                 input_address)

    (tx_id, fee, amount) = tcr.tcr.transfer_utxo_ada(cardano, src_wallet, utxo_obj, destination)

    logger.info('Refund TXID = {}, fee = {}, amount = {}'.format(tx_id, fee, amount))

if __name__ == '__main__':
    main()
