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
import traceback
from datetime import datetime

from tcr.database import Database
from tcr.cardano import Cardano
from tcr.nft import Nft
from tcr.wallet import Wallet
from tcr.wallet import WalletExternal
from tcr.metadata_list import MetadataList
import tcr.command
import tcr.tcr
import tcr.words

logger = None

def setup_logging(network: str, application: str) -> None:
    # Setup logging INFO and higher goes to the console.  DEBUG and higher goes to file
    global logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    console_handler.setFormatter(console_format)

    log_file = 'log/{}/{}_{}.log'.format(network, application, datetime.now().strftime("%Y%m%d_%H%M%S"))
    print('Log File: {}'.format(log_file))
    file_handler = logging.FileHandler(log_file)
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
        series_metametadata['self'] = metametadata_file
    return series_metametadata

def set_metametadata(cardano: Cardano, series_metametadata: Dict) -> None:
    drop_name = series_metametadata['drop-name']
    metametadata_file = 'nft/{}/{}/{}_metametadata.json'.format(cardano.get_network(), drop_name, drop_name)
    logger.info('Save MetaMetaData: {}'.format(metametadata_file))
    with open(metametadata_file, 'w') as file:
        file.write(json.dumps(series_metametadata, indent=4))

def get_series_metadata_set_file(cardano: Cardano, policy_name: str, drop_name: str) -> str:
    # get the remaining NFTs in the drop.  Generate the file if it doesn't exist
    metadata_set_file = 'nft/{}/{}/{}.json'.format(cardano.get_network(), drop_name, drop_name)
    logger.debug('Metadata Set File = {}'.format(metadata_set_file))
    if not os.path.isfile(metadata_set_file):
        logger.error('Series Metadata Set: {}, does not exist!'.format(metadata_set_file))
        raise Exception('Series Metadata Set: {}, does not exist!'.format(metadata_set_file))

    return metadata_set_file

def create_series_metadata_set_file(cardano: Cardano,
                                    policy_name: str,
                                    drop_name: str) -> str:
    metadata_set_file = 'nft/{}/{}/{}.json'.format(cardano.get_network(), drop_name, drop_name)

    if os.path.isfile(metadata_set_file):
        logger.error('Series Metadata Set: {}, already exists!'.format(metadata_set_file))
        raise Exception('Series Metadata Set: {}, already exists!'.format(metadata_set_file))

    series_metametadata = get_metametadata(cardano, drop_name)
    series_metametadata['policy'] = policy_name
    #codewords = tcr.words.generate_word_list('words.txt', 500)
    codewords = None
    files = Nft.create_series_metadata_set(cardano.get_network(),
                                           cardano.get_policy_id(policy_name),
                                           series_metametadata,
                                           codewords)
    series_metametadata = set_metametadata(cardano, series_metametadata)
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
    parser.add_argument('--burn',   required=False,
                                    action='store_true',
                                    default=False,
                                    help='Burn the token named at the policy.  Requires --wallet, --policy, --token')
    parser.add_argument('--confirm', required=False,
                                     action='store_true',
                                     default=False,
                                     help='Confirm burn all tokens in policy')
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
    parser.add_argument('--token',  required=False,
                                    action='store',
                                    metavar='NAME',
                                    default=None,
                                    help='The token to burn or empty to burn all in the policy')

    args = parser.parse_args()
    network = args.network
    create_wallet = args.create_wallet
    create_policy = args.create_policy
    create_drop = args.create_drop
    create_drop_template = args.create_drop_template
    mint = args.mint
    burn = args.burn
    wallet_name = args.wallet
    policy_name = args.policy
    drop_name = args.drop
    token_name = args.token
    confirm = args.confirm

    setup_logging(network, 'nftmint')
    logger = logging.getLogger(network)

    if not network in tcr.command.networks:
        logger.error('Invalid Network: {}'.format(network))
        raise Exception('Invalid Network: {}'.format(network))

    # Setup connection to cardano node, cardano wallet, and cardano db sync
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))
    database = Database('{}.ini'.format(network))

    logger.info('{} Payment Processor / NFT Minter'.format(network.upper()))
    logger.info('Copyright 2021 Kristofer Henderson & thecardroom.io')
    logger.info('Network: {}'.format(network))

    if create_wallet != None or create_policy != None or mint or burn:
        tip = cardano.query_tip()
        cardano.query_protocol_parameters()
        database.open()
        tip_slot = tip['slot']

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

        cardano.create_new_policy_id(tip_slot+tcr.SECONDS_PER_MONTH * 6,
                                     policy_wallet,
                                     create_policy)

        if cardano.get_policy_id(create_policy) == None:
            logger.error('Failed to create policy: <{}>'.format(create_policy))
            raise Exception('Failed to create policy: <{}>'.format(create_policy))

        logger.info('Successfully created new policy: {} / {}'.format(create_policy, cardano.get_policy_id(create_policy)))
        logger.info('Expires at slot: {}'.format(tip_slot+(tcr.SECONDS_PER_MONTH * 6)))
    elif create_drop != None:
        if (create_wallet != None or create_policy != None or
                create_drop_template != None or mint == True or wallet_name != None or
                drop_name != None):
            logger.error('--create-drop <NAME>, Requires only --policy')
            raise Exception('--create-drop <NAME>, Requires only --policy')

        if (policy_name == None):
            logger.error('--create-drop <NAME>, Requires --policy')
            raise Exception('--create-drop <NAME>, Requires --policy')

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
            logger.error('--mint, Requires --drop')
            raise Exception('--mint, Requires --drop')

        if (drop_name == None):
            logger.error('--mint, Requires --drop')
            raise Exception('--mint, Requires --drop')

        if (wallet_name != None or policy_name != None):
            logger.error('--mint, Wallet and policy derived from metadata')
            raise Exception('--mint, Wallet and policy derived from metadata')

        metametadata = get_metametadata(cardano, drop_name)
        policy_name = metametadata['policy']

        # Set the policy name
        logger.info('Policy: {}'.format(policy_name))
        if cardano.get_policy_id(policy_name) == None:
            logger.error('Policy: {}, does not exist'.format(policy_name))
            raise Exception('Policy: {}, does not exist'.format(policy_name))

        # Initialize the wallet
        wallet_name = cardano.get_policy_owner(policy_name)
        mint_wallet = Wallet(wallet_name, cardano.get_network())
        logger.info('Mint Wallet: {}'.format(wallet_name))
        if not mint_wallet.exists():
            logger.error('Wallet: {}, does not exist'.format(wallet_name))
            raise Exception('Wallet: {}, does not exist'.format(wallet_name))

        metadata_set_file = get_series_metadata_set_file(cardano, policy_name, drop_name)
        logger.info('Metadata Set File: {}'.format(metadata_set_file))

        # verify the metadata for each NFT
        metadatalist = MetadataList(metadata_set_file)
        while metadatalist.get_remaining() > 0:
            nftmd = Nft.parse_metadata_file(metadatalist.peek_next_file())
            if len(nftmd['token-names']) != 1:
                logger.error('There should only be one token name')
                raise Exception('There should only be one token name')

            if nftmd['policy-id'] != cardano.get_policy_id(policy_name):
                logger.error('Policy ID mismatch')
                raise Exception('Policy ID mismatch')

            token = nftmd['token-names'][0]
            if not nftmd['properties'][token]['image'].startswith('ipfs://'):
                logger.error('Image not uploaded to IPFS')
                raise Exception('Image not uploaded to IPFS')
        metadatalist.revert()

        # Set prices for the drop from metametadata file.  JSON stores keys as strings
        # so convert the keys to integers
        metametadata = get_metametadata(cardano, drop_name)
        prices = {}
        for price in metametadata['prices']:
            prices[int(price)] = metametadata['prices'][price]
        logger.info('prices: {}'.format(prices))

        max_per_tx = metametadata['max_per_tx']

        try:
            # Listen for incoming payments and mint NFTs when a UTXO matching a payment
            # value is found
            tcr.process_incoming_payments(cardano,
                                          database,
                                          mint_wallet,
                                          policy_name,
                                          drop_name,
                                          metadata_set_file,
                                          prices,
                                          max_per_tx)
        except Exception as e:
            logger.exception("Caught Exception")
    elif burn == True:
        # Set the policy name
        policy_id = cardano.get_policy_id(policy_name)
        logger.info('Policy: {}'.format(policy_name))
        if cardano.get_policy_id(policy_name) == None:
            logger.error('Policy: {}, does not exist'.format(policy_name))
            raise Exception('Policy: {}, does not exist'.format(policy_name))

        # Initialize the wallet
        wallet_name = cardano.get_policy_owner(policy_name)
        burn_wallet = Wallet(wallet_name, cardano.get_network())
        logger.info('Burn Wallet: {}'.format(wallet_name))
        if not burn_wallet.exists():
            logger.error('Wallet: {}, does not exist'.format(wallet_name))
            raise Exception('Wallet: {}, does not exist'.format(wallet_name))

        if token_name == None and confirm:
            #burn all
            token_names = []
            (utxos, lovelace) = cardano.query_utxos(burn_wallet)
            utxos = cardano.query_utxos_time(database, utxos)
            utxos.sort(key=lambda item : item['slot-no'])

            utxo_in = None
            input_utxos = []
            for utxo in utxos:
                for a in utxo['assets']:
                    if a.startswith('{}.'.format(policy_id)):
                        if len(token_names) < 200:
                            utxo_in = utxo
                            token_name = a.split('.')[1]
                            token_names.append(token_name)
                            if not utxo in input_utxos:
                                input_utxos.append(utxo)

            if len(token_names) > 0:
                tcr.burn_nft_internal(cardano, burn_wallet, policy_name, input_utxos, token_names, token_amount=1)
                while cardano.contains_txhash(burn_wallet, utxo_in['tx-hash']):
                    logger.info('wait')
                    time.sleep(10)
            else:
                logger.error('No tokens found for policy')
        elif token_name != None:
            # burn just the specified token in the specified policy
            token_names = []
            (utxos, lovelace) = cardano.query_utxos(burn_wallet)
            utxos = cardano.query_utxos_time(database, utxos)
            utxos.sort(key=lambda item : item['slot-no'])

            utxo_in = None
            input_utxos = []
            for utxo in utxos:
                for a in utxo['assets']:
                    if a == '{}.{}'.format(policy_id, token_name):
                        token_names.append(token_name)
                        if not utxo in input_utxos:
                            input_utxos.append(utxo)

            tcr.burn_nft_internal(cardano, burn_wallet, policy_name, input_utxos, token_names, token_amount=1)
        else:
            logger.error('Nothing to do')

    else:
        logger.info('')
        logger.info('Help:')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-wallet=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-policy=<name> --wallet=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-drop=<name> --policy=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --create-drop-template=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --mint --wallet=<name> --policy=<name> --drop=<name>')
        logger.info('\t$ nftmint --network=<testnet | mainnet> --burn --wallet=<name> --policy=<name> [--confirm | --token=<name>]')

    database.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
