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
parser.add_argument('--network', required=True,
                                 action='store',
                                 type=str,
                                 metavar='NAME',
                                 help='Which network to use, [mainnet | testnet]')
parser.add_argument('--wallet',  required=False,
                                 action='store',
                                 type=str,
                                 default=None,
                                 metavar='NAME',
                                 help='Dump UTXOs from wallet')
parser.add_argument('--policy',  required=False,
                                 action='store',
                                 type=str,
                                 default=None,
                                 metavar='NAME',
                                 help='')
args = parser.parse_args()
network = args.network
wallet_name = args.wallet
policy_name = args.policy

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

wallet = None
if wallet_name != None:
    wallet = Wallet(wallet_name, cardano.get_network())

    if not wallet.exists():
        logger.error('Wallet: <{}> does not exist'.format(wallet_name))
        raise Exception('Wallet: <{}> does not exist'.format(wallet_name))

    cardano.dump_utxos(wallet)

    (utxos, lovelace) = cardano.query_utxos(wallet)
    utxos = cardano.query_utxos_time(database, utxos)
    utxos.sort(key=lambda item : item['slot-no'])
    for utxo in utxos:
        logger.info('{} {}: {} = {} lovelace'.format(utxo['time'], utxo['slot-no'], utxo['tx-hash'], utxo['amount']))

if policy_name != None:
    stake_address = database.query_stake_address(wallet.get_payment_address())
    logger.info('      address = {}'.format(wallet.get_payment_address()))
    logger.info('Stake address = {}'.format(stake_address))

    logger.info('')

    if cardano.get_policy_id(policy_name) == None:
        logger.error('Policy: <{}> does not exist'.format(policy_name))
        raise Exception('Policy: <{}> does not exist'.format(policy_name))

    tokens = database.query_current_owner(cardano.get_policy_id(policy_name))
    logger.info("By Token: ")
    logger.info('len = {}'.format(len(tokens)))
    by_address = {}
    for name in tokens:
        address = tokens[name]['address']
        slot = tokens[name]['slot']
        logger.info('{} owned by {} at slot {}'.format(name, address, slot))

        if address in by_address:
            by_address[address].append(name)
        else:
            by_address[address] = [name]

    holders = list(by_address.items())
    def sort_by_length(item):
        return len(item[1])
    holders.sort(key=sort_by_length)
    logger.info('')
    logger.info('')
    logger.info('By Owner:')
    logger.info('len = {}'.format(len(holders)))
    for holder in holders:
        logger.info('{}({})= {}'.format(holder[0], len(holder[1]), holder[1]))
