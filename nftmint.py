#
# Copyright 2021 Kristofer Henderson
#
# This file not licensed for use.  Use of this file will cause your private
# keys and mnemonic seed phrase to be stolen and all your crypto lost!
#

from typing import Dict
import argparse
import json
import logging
import os
import time

from database import Database
from cardano import Cardano
from nft import Nft
from wallet import Wallet
from wallet import WalletExternal
import command
import tcr
import words

logger = None

def setup_logging(network) -> None:
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

def get_metametadata(cardano: Cardano, drop_name: str) -> Dict:
    series_metametadata = {}
    metametadata_file = 'nft/{}/{}_metametadata.json'.format(cardano.get_network(), drop_name)
    logger.info('Open MetaMetaData: {}'.format(metametadata_file))
    with open(metametadata_file, 'r') as file:
        series_metametadata = json.load(file)
        if drop_name != series_metametadata['drop-name']:
            raise Exception('Unexpected Drop Name: {} vs {}'.format(drop_name, series_metametadata['drop-name']))
    return series_metametadata

def get_series_metadata_set_file(cardano: Cardano, policy_name: str, drop_name: str, allow_new: bool=False) -> str:
    # get the remaining NFTs in the drop.  Generate the file if it doesn't exist
    metadata_set_file = 'nft/{}/{}.json'.format(cardano.get_network(), drop_name)
    logger.info('Open Series MetaData: {}'.format(metadata_set_file))
    if not os.path.isfile(metadata_set_file):
        if allow_new:
            series_metametadata = get_metametadata(cardano, drop_name)
            codewords = words.generate_word_list('words.txt', 500)
            files = Nft.create_series_metadata_set(cardano.get_network(),
                                                   cardano.get_policy_id(policy_name),
                                                   series_metametadata,
                                                   codewords)
            metadata_set = {'files': files}
            with open(metadata_set_file, 'w') as file:
                file.write(json.dumps(metadata_set, indent=4))
        else:
            logger.error('Allow New = False, Series Metadata Set: {}, does not exist!'.format(metadata_set_file))
            raise Exception('Allow New = False, Series Metadata Set: {}, does not exist!'.format(metadata_set_file))

    return metadata_set_file

def main():
    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network',   required=True,
                                       action='store',
                                       metavar='NAME',
                                       help='Which network to use, [mainnet | testnet]')
    parser.add_argument('--policy',    required=True,
                                       action='store',
                                       metavar='NAME',
                                       help='The name of the policy for minting.')
    parser.add_argument('--wallet',    required=True,
                                       action='store',
                                       metavar='NAME',
                                       help='The name of the wallet for accepting payment and minting.')
    parser.add_argument('--drop',      required=True,
                                       action='store',
                                       metavar='NAME',
                                       help='The name of the NFT drop.')
    parser.add_argument('--allow-new', default=False,
                                       action='store_true',
                                       required=False,
                                       help='Allow a new policy and or drop file to be created')

    args = parser.parse_args()

    network = args.network
    drop_name = args.drop
    policy_name = args.policy
    wallet_name = args.wallet
    allow_new = args.allow_new

    setup_logging(network)

    if not network in command.networks:
        logger.error('Invalid Network: {}'.format(network))
        raise Exception('Invalid Network: {}'.format(network))

    # Setup connection to cardano node, cardano wallet, and cardano db sync
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

    logger.info('{} Payment Processor / NFT Minter'.format(network.upper()))
    logger.info('Allow Create New Objects: {}'.format(allow_new))
    logger.info('Network: {}'.format(network))
    logger.info('Policy: {} / {}'.format(policy_name, cardano.get_policy_id(policy_name)))
    logger.info('Wallet: {}'.format(wallet_name))
    logger.info('Drop: {}'.format(drop_name))

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))

    database = Database('{}.ini'.format(network))
    meta = database.query_chain_metadata()
    db_size = database.query_database_size()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.debug('Database Chain Metadata: {} / {}'.format(meta[1], meta[2]))
    logger.debug('Database Size: {}'.format(db_size))
    logger.info('Database Latest Slot: {}'.format(latest_slot))
    logger.info('Sync Progress: {}'.format(sync_progress))

    metadata_set_file = get_series_metadata_set_file(cardano, policy_name, drop_name, allow_new)

    # Initialize the wallet, assume it already exists
    mint_wallet = Wallet(wallet_name, cardano.get_network())
    logger.info('Mint Wallet: {}'.format(wallet_name))
    if not mint_wallet.exists():
        logger.error('Wallet: {}, does not exist'.format(wallet_name))
        raise Exception('Wallet: {}, does not exist'.format(wallet_name))

    # Set the policy name and create it if it doesn't exist
    logger.info('Policy: {}'.format(policy_name))
    if cardano.get_policy_id(policy_name) == None:
        if allow_new:
            logger.info('\"{}\" Does Not Exist.  Create New.'.format(policy_name))
            cardano.create_new_policy_id(tip_slot+tcr.SECONDS_PER_YEAR, mint_wallet, policy_name)
            logger.info('Created Policy: \"{}\" : ID={}'.format(policy_name, cardano.get_policy_id(policy_name)))
            logger.info('Policy Will Expire at SLOT: {}'.format(tip_slot + tcr.SECONDS_PER_YEAR))
        else:
            logger.error('Allow New = False, Policy: {}, does not exist'.format(policy_name))
            raise Exception('Allow New = False, Policy: {}, does not exist'.format(policy_name))

    # Set prices for the drop from metametadata file.  JSON stores keys as strings
    # so convert the keys to integers
    metametadata = get_metametadata(cardano, drop_name)
    prices = {}
    for price in metametadata['prices']:
        prices[int(price)] = metametadata['prices'][price]
    logger.debug('prices: {}'.format(prices))

    try:
        # Listen for incoming payments and mint NFTs when a UTXO matching a payment
        # value is found
        tcr.process_incoming_payments(cardano,
                                      database,
                                      mint_wallet,
                                      policy_name,
                                      metadata_set_file,
                                      prices)
    except Exception as e:
        logger.exception("Caught Exception")

    database.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
