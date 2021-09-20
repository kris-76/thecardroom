#
# Copyright 2021 Kristofer Henderson
#
# This file not licensed for use.
#

from wallet import Wallet
from cardano import Cardano
from database import Database
import logging
import argparse
import command
import datetime
import nftmint

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--network',   required=True,
                                    action='store',
                                    metavar='NAME',
                                    help='Which network to use, [mainnet | testnet]')
args = parser.parse_args()
network = args.network

if not network in command.networks:
    raise Exception('Invalid Network: {}'.format(network))

nftmint.setup_logging(network, 'status')
logger = logging.getLogger(network)

cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

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

if cardano.get_network() == 'mainnet':
    wallet = Wallet('tcr_mint', cardano.get_network())

    stake_address = database.query_stake_address(wallet.get_payment_address())
    logger.info('      address = {}'.format(wallet.get_payment_address()))
    logger.info('Stake address = {}'.format(stake_address))

    logger.info('')

    tokens = database.query_current_owner('2b9fb283d8116489f4a494e76c75efe0d9992aaef6c65eaf9b374298')
    print("By Token: ")
    print('len = {}'.format(len(tokens)))
    by_address = {}
    for name in tokens:
        address = tokens[name]['address']
        slot = tokens[name]['slot']
        print('{} owned by {} at slot {}'.format(name, address, slot))

        if address in by_address:
            by_address[address].append(name)
        else:
            by_address[address] = [name]

    holders = list(by_address.items())
    def sort_by_length(item):
        return len(item[1])
    holders.sort(key=sort_by_length)
    print('')
    print('')
    print('By Owner:')
    print('len = {}'.format(len(holders)))
    for holder in holders:
        print('{}({})= {}'.format(holder[0], len(holder[1]), holder[1]))
