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

def setup_logging(network: str, application: str) -> None:
    # Setup logging INFO and higher goes to the console.  DEBUG and higher goes to file
    global logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    console_handler.setFormatter(console_format)

    file_handler = logging.FileHandler('log/{}_{}_{}.log'.format(network, application, round(time.time())))
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    file_handler.setFormatter(file_format)

    logger_names = [network, 'tcr', 'nft', 'cardano', 'wallet', 'command', 'database', 'metadata-list']
    for logger_name in logger_names:
        other_logger = logging.getLogger(logger_name)
        other_logger.setLevel(logging.DEBUG)
        other_logger.addHandler(console_handler)
        other_logger.addHandler(file_handler)

    logger = logging.getLogger(network)

def get_metametadata(cardano: Cardano, drop_name: str) -> Dict:
    series_metametadata = {}
    metametadata_file = 'nft/{}/{}/{}_metametadata.json'.format(cardano.get_network(), drop_name, drop_name)
    logger.info('Open MetaMetaData: {}'.format(metametadata_file))
    with open(metametadata_file, 'r') as file:
        series_metametadata = json.load(file)
        if drop_name != series_metametadata['drop-name']:
            raise Exception('Unexpected Drop Name: {} vs {}'.format(drop_name, series_metametadata['drop-name']))
    return series_metametadata

def get_series_metadata_set_file(cardano: Cardano, policy_name: str, drop_name: str) -> str:
    # get the remaining NFTs in the drop.  Generate the file if it doesn't exist
    metadata_set_file = 'nft/{}/{}/{}.json'.format(cardano.get_network(), drop_name, drop_name)
    logger.info('Open Series MetaData: {}'.format(metadata_set_file))
    if not os.path.isfile(metadata_set_file):
        logger.error('Series Metadata Set: {}, does not exist!'.format(metadata_set_file))
        raise Exception('Series Metadata Set: {}, does not exist!'.format(metadata_set_file))

    return metadata_set_file

def create_series_metadata_set_file(cardano: Cardano, policy_name: str, drop_name: str) -> str:
    metadata_set_file = 'nft/{}/{}/{}.json'.format(cardano.get_network(), drop_name, drop_name)

    if os.path.isfile(metadata_set_file):
        logger.error('Series Metadata Set: {}, already exists!'.format(metadata_set_file))
        raise Exception('Series Metadata Set: {}, already exists!'.format(metadata_set_file))

    series_metametadata = get_metametadata(cardano, drop_name)
    codewords = words.generate_word_list('words.txt', 500)
    files = Nft.create_series_metadata_set(cardano.get_network(),
                                           cardano.get_policy_id(policy_name),
                                           series_metametadata,
                                           codewords)
    metadata_set = {'files': files}
    with open(metadata_set_file, 'w') as file:
        file.write(json.dumps(metadata_set, indent=4))

    return metadata_set_file

def main():
    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network',       required=True,
                                           action='store',
                                           metavar='NAME',
                                           help='Which network to use, [mainnet | testnet]')
    parser.add_argument('--create-wallet', required=False,
                                           action='store',
                                           metavar='NAME',
                                           default=None,
                                           help='Create a new wallet for <network>.  No other parameters required.')
    parser.add_argument('--create-policy', required=False,
                                           action='store',
                                           metavar='NAME',
                                           default=None,
                                           help='Create a new policy on <network> for <wallet>.  Requires --wallet')
    parser.add_argument('--create-drop',   required=False,
                                           action='store',
                                           metavar='NAME',
                                           default=None,
                                           help='Create a new drop on <network> for <policy> and <wallet>.  Requires --policy, --wallet')
    parser.add_argument('--create-drop-template', required=False,
                                                  action='store',
                                                  metavar='NAME',
                                                  default=None,
                                                  help='')
    parser.add_argument('--mint',   required=False,
                                    action='store_true',
                                    default=False,
                                    help='Process payments, mint NFTs.  Requires --wallet, --policy, --drop')
    parser.add_argument('--policy', required=False,
                                    action='store',
                                    metavar='NAME',
                                    default=None,
                                    help='The name of the policy for minting.')
    parser.add_argument('--wallet', required=False,
                                    action='store',
                                    metavar='NAME',
                                    default=None,
                                    help='The name of the wallet for accepting payment and minting.')
    parser.add_argument('--drop',   required=False,
                                    action='store',
                                    metavar='NAME',
                                    default=None,
                                    help='The name of the NFT drop.')

    args = parser.parse_args()
    network = args.network
    create_wallet = args.create_wallet
    create_policy = args.create_policy
    create_drop = args.create_drop
    create_drop_template = args.create_drop_template
    mint = args.mint
    wallet_name = args.wallet
    policy_name = args.policy
    drop_name = args.drop

    setup_logging(network, 'nftmint')
    logger = logging.getLogger(network)

    if not network in command.networks:
        logger.error('Invalid Network: {}'.format(network))
        raise Exception('Invalid Network: {}'.format(network))

    # Setup connection to cardano node, cardano wallet, and cardano db sync
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

    logger.info('{} Payment Processor / NFT Minter'.format(network.upper()))
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


    # Run commands specified in the command parameters and verify valid input
    if create_wallet != None:
        if (create_policy != None or create_drop != None or
                create_drop_template != None or mint == True or drop_name != None or
                policy_name != None or wallet_name != None):
            logger.error('--create-wallet <NAME>, Does not permit other parameters')
            raise Exception('--create-wallet <NAME>, Does not permit other parameters')

        new_wallet = Wallet(create_wallet, cardano.get_network())
        if new_wallet.exists():
            logger.error('Wallet: <{}> already exists'.format(create_wallet))
            raise Exception('Wallet: <{}> already exists'.format(create_wallet))

        if not new_wallet.setup_wallet(save_extra_files=True):
            logger.error('Failed to create wallet: <{}>'.format(create_wallet))
            raise Exception('Failed to create wallet: <{}>'.format(create_wallet))

        logger.info('Successfully created new wallet: <{}>'.format(create_wallet))
    elif create_policy != None:
        if (create_wallet != None or create_drop != None or create_drop_template != None or
                mint == True or policy_name != None or drop_name != None):
            logger.error('--create-policy=<NAME>, Requires only --wallet')
            raise Exception('--create-policy=<NAME>, Requires only --wallet')

        if (wallet_name == None):
            logger.error('--create-policy=<NAME>, Requires --wallet')
            raise Exception('--create-policy=<NAME>, Requires --wallet')

        if cardano.get_policy_id(create_policy) != None:
            logger.error('Policy: <{}> already exists'.format(create_policy))
            raise Exception('Policy: <{}> already exists'.format(create_policy))

        policy_wallet = Wallet(wallet_name, cardano.get_network())
        if not policy_wallet.exists():
            logger.error('Wallet: <{}> does not exist'.format(wallet_name))
            raise Exception('Wallet: <{}> does not exist'.format(wallet_name))

        cardano.create_new_policy_id(tip_slot+tcr.SECONDS_PER_YEAR,
                                     policy_wallet,
                                     create_policy)

        if cardano.get_policy_id(create_policy) == None:
            logger.error('Failed to create policy: <{}>'.format(create_policy))
            raise Exception('Failed to create policy: <{}>'.format(create_policy))

        logger.info('Successfully created new policy: {} / {}'.format(create_policy, cardano.get_policy_id(create_policy)))
        logger.info('Expires at slot: {}'.format(tip_slot+tcr.SECONDS_PER_YEAR))
    elif create_drop != None:
        if (create_wallet != None or create_policy != None or
                create_drop_template != None or mint == True or wallet_name != None or
                drop_name != None):
            logger.error('--create-drop <NAME>, Requires only --policy')
            raise Exception('--create-drop <NAME>, Requires only --policy')

        if (policy_name == None):
            logger.error('--create-policy <NAME>, Requires --policy')
            raise Exception('--create-policy <NAME>, Requires --policy')

        if cardano.get_policy_id(policy_name) == None:
            logger.error('Policy: <{}> does not exist'.format(create_policy))
            raise Exception('Policy: <{}> does not exist'.format(create_policy))

        metadata_set_file = create_series_metadata_set_file(cardano, policy_name, create_drop)
        logger.info('Successfully created new drop: {} '.format(metadata_set_file))
    elif create_drop_template != None:
        logger.info('TODO')

    elif mint == True:
        if (create_wallet != None or create_policy != None or create_drop != None or
                create_drop_template != None):
            logger.error('--mint, Requires --wallet, --policy, --drop')
            raise Exception('--mint, Requires --wallet, --policy, --drop')

        if (wallet_name == None or policy_name == None or drop_name == None):
            logger.error('--mint, Requires --wallet, --policy, --drop')
            raise Exception('--mint, Requires --wallet, --policy, --drop')

        # Initialize the wallet
        mint_wallet = Wallet(wallet_name, cardano.get_network())
        logger.info('Mint Wallet: {}'.format(wallet_name))
        if not mint_wallet.exists():
            logger.error('Wallet: {}, does not exist'.format(wallet_name))
            raise Exception('Wallet: {}, does not exist'.format(wallet_name))

        # Set the policy name
        logger.info('Policy: {}'.format(policy_name))
        if cardano.get_policy_id(policy_name) == None:
            logger.error('Policy: {}, does not exist'.format(policy_name))
            raise Exception('Policy: {}, does not exist'.format(policy_name))

        metadata_set_file = get_series_metadata_set_file(cardano, policy_name, drop_name)
        logger.info('Metadata Set File: {}'.format(metadata_set_file))

        # Set prices for the drop from metametadata file.  JSON stores keys as strings
        # so convert the keys to integers
        metametadata = get_metametadata(cardano, drop_name)
        prices = {}
        for price in metametadata['prices']:
            prices[int(price)] = metametadata['prices'][price]
        logger.info('prices: {}'.format(prices))

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
    else:
        logger.info('')
        logger.info('Help:')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-wallet=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-policy=<name> --wallet=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-drop=<name> --policy=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-drop-template=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --mint --wallet=<name> --policy=<name> --drop=<name>')

    database.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Caught Exception!")
        print(e)
