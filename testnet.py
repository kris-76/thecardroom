#
# Copyright 2021 Kristofer Henderson
#
# This file not licensed for use.  Use of this file will cause your private
# keys and mnemonic seed phrase to be stolen and all your crypto lost!
#

from wallet import Wallet
from wallet import WalletExternal
from cardano import Cardano
from nft import Nft
import tcr
from database import Database
import random
import json
import os

# Setup connection to cardano node, cardano wallet, and cardano db sync

cardano = Cardano('testnet', 'testnet_protocol_parameters.json')
tip = cardano.query_tip()
tip_slot = tip['slot']
print('Cardano Node Tip Slot: {}'.format(tip_slot))

cardano.query_protocol_parameters()

database = Database('testnet.ini')
meta = database.query_chain_metadata()
print('{} / {}'.format(meta[1], meta[2]))

db_size = database.query_database_size()
print('Database Size: {}'.format(db_size))

latest_slot = database.query_latest_slot()
print('Database Latest Slot: {}'.format(latest_slot))

sync_progress = database.query_sync_progress()
print('Sync Progress: {}'.format(sync_progress))


# Define some metadata that can be used to generate a series
series_metadata = {
    'series': 2,
    'drop-name': 'testnet_series_2',
    'init-nft-id': 1,
    'token-name': 'TNx{:03}x{:02}x{}',
    'nft-name': 'Test Net {}.{} [{}/{}]',

    'cards': [
        # NFT1
        {
            'id': 1,
            'count': 2,
            'image': 'ipfs://Qmd4KNJQiy6eeiGAdDQ7ZkYC6Wju5T81XawfZnEw2uXcHg',
            'description': 'The First Description of the NFT',
            'properties': {'author': 'TestNet', 'location': 'The Moon', 'rarity': 'Epic', 'id': None}
        },

        # NFT2
        {
            'id': 2,
            'count': 3,
            'image': 'ipfs://Qmdz4jAK6WxVZpkEMHLpWmwNSgeq3dkTYZsWKsjPwE5GU5',
            'description': 'The Second Description of the NFT',
            'properties': {'author': 'TestNet', 'location': 'Outer Space', 'rarity': 'Rare', 'id': None}
        },

        # NFT3
        {
            'id': 3,
            'count': 4,
            'image': 'ipfs://Qmbx1Tf8T9H53BkjMWQrHbJV7qMNCKdiNx8ykLHSnrRazz',
            'description': 'The Third Description of the NFT',
            'properties': {'author': 'TestNet', 'location': 'Dungeon', 'rarity': 'Uncommon', 'id': None}
        },

        # NFT4
        {
            'id': 4,
            'count': 5,
            'image': 'ipfs://QmZvPCVTsneutpb9N72qT5uHzjav83StQJzDJT4zqad9QS',
            'description': 'The Fourth Description of the NFT',
            'properties': {'author': 'TestNet', 'location': 'Under The Sea', 'rarity': 'Common', 'id': None}
        }
    ]
}

# Create the wallet, assume it already exists
testnet1 = Wallet("testnet1", cardano.get_network())

# Set the policy name and create it if it doesn't exist
policy_name = 'tn_policy1'
if cardano.get_policy_id(policy_name) == None:
    cardano.create_new_policy_id(tip_slot+10000000, testnet1, policy_name)

# get the remaining NFTs in the drop.  Generate the file if it doesn't exist
metadata_set_file = '{}.json'.format(series_metadata['drop-name'])
if not os.path.exists(metadata_set_file):
    files = Nft.create_series_metadata_set(cardano.get_network(),
                                           cardano.get_policy_id(policy_name),
                                           series_metadata)
    random.shuffle(files)
    metadata_set = {}
    metadata_set['files'] = files

    with open(metadata_set_file, 'w') as file:
        file.write(json.dumps(metadata_set, indent=4))

# Define prices for the drop.  25 ADA buys 1 random NFT.
# 85 ADA buys 4 random NFTs
prices = {
    25000000: 1,
    85000000: 4
}

print("Processing NFT Payments under policy: {}".format(policy_name))
# Listen for incoming payments and mint NFTs when a UTXO matching a payment
# value is found
tcr.process_incoming_payments(cardano,
                              database,
                              testnet1,
                              policy_name,
                              metadata_set_file,
                              prices)

database.close()
