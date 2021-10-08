#
# Copyright 2021 Kristofer Henderson
#
# This file not licensed for use.
#

from tcr.wallet import Wallet
from tcr.cardano import Cardano
from tcr.database import Database
import logging
import argparse
import tcr.command
import tcr.nftmint

def main():
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

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'status')
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

        stake_address = database.query_stake_address(wallet.get_payment_address())
        logger.info('      address = {}'.format(wallet.get_payment_address()))
        logger.info('Stake address = {}'.format(stake_address))

        cardano.dump_utxos_sorted(database, wallet)

    if policy_name != None:
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


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
