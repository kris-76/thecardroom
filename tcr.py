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

"""
File: tcr.py
Author: Kris Henderson
"""

from typing import Dict

from nft import Nft
from cardano import Cardano
from wallet import Wallet
from wallet import WalletExternal
from database import Database
import json
import random
import time

DAYS_PER_YEAR = int(365)
MONTHS_PER_YEAR = int(12)
MINUTES_PER_HOUR = int(60)
HOURS_PER_DAY = int(24)
SECONDS_PER_MINUTE = int(60)

SECONDS_PER_HOUR = int(MINUTES_PER_HOUR * SECONDS_PER_MINUTE)
SECONDS_PER_DAY = int(HOURS_PER_DAY * SECONDS_PER_HOUR)
SECONDS_PER_MONTH = int((DAYS_PER_YEAR / MONTHS_PER_YEAR) * SECONDS_PER_DAY)
SECONDS_PER_YEAR = int(MONTHS_PER_YEAR * SECONDS_PER_MONTH)

def transfer_all_assets(cardano: Cardano,
                        from_wallet: Wallet,
                        to_wallet: Wallet) -> None:
    """
    Transfer all assets (lovelace and other tokens) from one wallet to another.
    """

    (from_utxos, from_total_lovelace) = cardano.query_utxos(from_wallet)
    # get all incoming assets from utxos
    incoming_assets = {}
    for utxo in from_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    print("From Total Lovelace: {}".format(from_total_lovelace))
    # Draft transaction for fee calculation
    outputs = [{'address': to_wallet.get_payment_address(),
                'amount': 1,
                'assets': incoming_assets}]
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos,
                                             outputs,
                                             fee,
                                             'transaction/transfer_all_assets_draft_tx')

    # Calculate fee & update values
    fee = cardano.calculate_min_fee('transaction/transfer_all_assets_draft_tx',
                                    len(from_utxos),
                                    len(outputs),
                                    1)
    outputs[0]['amount'] = from_total_lovelace - fee

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos,
                                             outputs,
                                             fee,
                                             'transaction/transfer_all_assets_unsigned_tx')

    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_all_assets_unsigned_tx',
                             from_wallet.get_signing_key_file(),
                             'transaction/transfer_all_assets_signed_tx')

    #submit
    cardano.submit_transaction('transaction/transfer_all_assets_signed_tx')

def transfer_ada(cardano: Cardano,
                 from_wallet: Wallet,
                 lovelace_amount: int,
                 to_wallet: Wallet) -> None:
    """
    Transfer lovelace from one wallet to another.
    """

    (from_utxos, from_total_lovelace) = cardano.query_utxos(from_wallet)
    # get all incoming assets from utxos
    incoming_assets = {}
    for utxo in from_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    print("From Total Lovelace: {}".format(from_total_lovelace))
    # Draft transaction for fee calculation
    outputs = [{'address': from_wallet.get_payment_address(), 'amount': 1, 'assets': incoming_assets},
               {'address': to_wallet.get_payment_address(), 'amount': 1, 'assets': {}}]
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos,
                                             outputs,
                                             fee,
                                             'transaction/transfer_ada_draft_tx')

    # Calculate fee & update values
    fee = cardano.calculate_min_fee('transaction/transfer_ada_draft_tx',
                                    len(from_utxos),
                                    len(outputs), 1)
    outputs[0]['amount'] = from_total_lovelace - lovelace_amount - fee
    outputs[1]['amount'] = lovelace_amount

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos,
                                             outputs,
                                             fee,
                                             'transaction/transfer_ada_unsigned_tx')

    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_ada_unsigned_tx',
                             from_wallet.get_signing_key_file(),
                             'transaction/transfer_ada_signed_tx')

    #submit
    cardano.submit_transaction('transaction/transfer_ada_signed_tx')

def transfer_nft(cardano: Cardano,
                 from_wallet: Wallet,
                 nft_assets: Dict[str, int],
                 to_wallet: Wallet) -> None:
    """
    Transfer an NFT from one wallet to another.

    Also transfers the minimum lovelace amount defined by the network parameters
    plus 1000000.  As of today, that is 2 ADA.
    """

    (from_utxos, from_total_lovelace) = cardano.query_utxos(from_wallet)
    # get all incoming assets from utxos
    incoming_assets = {}
    incoming_lovelace = 0
    for utxo in from_utxos:
        incoming_lovelace += utxo['amount']
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    # subtract outgoing assets
    for a in nft_assets:
        incoming_assets[a] -= nft_assets[a]
        if incoming_assets[a] < 0:
            raise Exception('Asset value less than zero.')

    print("From Total Lovelace: {}".format(from_total_lovelace))
    # Draft transaction for fee calculation
    outputs = [{'address': from_wallet.get_payment_address(), 'amount': 1, 'assets': incoming_assets},
               {'address': to_wallet.get_payment_address(), 'amount': 1, 'assets': nft_assets}]

    #draft
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos,
                                             outputs,
                                             fee,
                                             'transaction/transfer_nft_draft_tx')

    # https://github.com/input-output-hk/cardano-ledger-specs/blob/master/doc/explanations/min-utxo.rst
    # minUTxOValue is the minimum value if sending ADA only.  Since ADA plus a
    # custom NFT token is being sent the amount to send is larger.  500000 extra
    # seems to be ok.  Make it 1000000 to be sure.
    min_utxo_value = cardano.get_min_utxo_value() + 1000000

    # Calculate fee & update values
    fee = cardano.calculate_min_fee('transaction/transfer_nft_draft_tx',
                                    len(from_utxos),
                                    len(outputs),
                                    1)
    if (incoming_lovelace - fee) < min_utxo_value:
        # hopefully still enough
        min_utxo_value = incoming_lovelace - fee

    print("Fee = {} lovelace".format(fee))
    outputs[0]['amount'] = from_total_lovelace - min_utxo_value - fee
    outputs[1]['amount'] = min_utxo_value

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos,
                                             outputs,
                                             fee,
                                             'transaction/transfer_nft_unsigned_tx')

    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_nft_unsigned_tx',
                             from_wallet.get_signing_key_file(),
                             'transaction/transfer_nft_signed_tx')

    #submit
    cardano.submit_transaction('transaction/transfer_nft_signed_tx')

def burn_nft_internal(cardano: Cardano,
                      burning_wallet: Wallet,
                      policy_name: str,
                      token_name: str) -> None:
    """
    Burn one NFT.
    """

    (burning_utxos, burning_total_lovelace) = cardano.query_utxos(burning_wallet)

    incoming_assets = {}
    for utxo in burning_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    # The NFT burned will be removed from the output when the transaction is created
    address_outputs = [{'address': burning_wallet.get_payment_address(),
                        'amount': 1, 'assets': incoming_assets}]
    fee = 0
    # draft
    cardano.create_burn_nft_transaction_file(burning_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             token_name,
                                             1,
                                             'transaction/burn_nft_internal_draft_tx')
    #fee
    fee = cardano.calculate_min_fee('transaction/burn_nft_internal_draft_tx',
                                    len(burning_utxos),
                                    1, 1)
    address_outputs[0]['amount'] = burning_total_lovelace - fee
    #final
    cardano.create_burn_nft_transaction_file(burning_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             token_name,
                                             1,
                                             'transaction/burn_nft_internal_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/burn_nft_internal_unsigned_tx',
                             burning_wallet.get_signing_key_file(),
                             'transaction/burn_nft_internal_signed_tx')
    #submit
    cardano.submit_transaction('transaction/burn_nft_internal_signed_tx')

def mint_nft_internal(cardano: Cardano,
                      minting_wallet: Wallet,
                      policy_name: str,
                      token_name: str) -> None:
    """
    Mint an NFT to the wallet that is minting it.
    """

    (minting_utxos, minting_total_lovelace) = cardano.query_utxos(minting_wallet)

    incoming_assets = {}
    for utxo in minting_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    # The NFT minted will be added to the output when the transaction is created
    address_outputs = [{'address': minting_wallet.get_payment_address(),
                        'amount': 1, 'assets': incoming_assets}]
    fee = 0
    # draft
    cardano.create_mint_nft_transaction_file(minting_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             token_name,
                                             1,
                                             'transaction/mint_nft_internal_draft_tx')
    #fee
    fee = cardano.calculate_min_fee('transaction/mint_nft_internal_draft_tx',
                                    len(minting_utxos),
                                    1, 1)
    print("Fee = {} lovelace".format(fee))
    address_outputs[0]['amount'] = minting_total_lovelace - fee
    #final
    cardano.create_mint_nft_transaction_file(minting_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             token_name,
                                             1,
                                             'transaction/mint_nft_internal_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/mint_nft_internal_unsigned_tx',
                             minting_wallet.get_signing_key_file(),
                             'transaction/mint_nft_internal_signed_tx')
    #submit
    cardano.submit_transaction('transaction/mint_nft_internal_signed_tx')

def mint_nft_external(cardano: Cardano,
                      minting_wallet: Wallet,
                      policy_name: str,
                      input_txhash: str,
                      nft_metadata_file: str,
                      destination_wallet: Wallet) -> None:
    """
    Mint an NFT to a different wallet.

    Also transfers the minimum lovelace amount as defined by the network protocol
    parameters plus 1000000.  Currently 2 ADA.
    """

    incoming_utxos = []
    (minting_utxos, minting_lovelace) = cardano.query_utxos(minting_wallet)

    incoming_assets = {}
    for utxo in minting_utxos:
        if utxo['tx-hash'] == input_txhash:
            incoming_utxos.append(utxo)
            for a in utxo['assets']:
                if a in incoming_assets:
                    incoming_assets[a] += utxo['assets'][a]
                else:
                    incoming_assets[a] = utxo['assets'][a]
            break

    # The NFT minted will be added to the output when the transaction is created
    address_outputs = [{
                            'address': minting_wallet.get_payment_address(),
                            'amount': 1, 'assets': incoming_assets
                       },
                       {
                           'address': destination_wallet.get_payment_address(),
                            'amount': 1, 'assets': {}
                        }]

    # draft
    fee = 0
    cardano.create_mint_nft_transaction_file(incoming_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             nft_metadata_file,
                                             1,
                                             'transaction/mint_nft_external_draft_tx')

    # https://github.com/input-output-hk/cardano-ledger-specs/blob/master/doc/explanations/min-utxo.rst
    # minUTxOValue is the minimum value if sending ADA only.  Since ADA plus a
    # custom NFT token is being sent the amount to send is larger.  500000 extra
    # seems to be ok.  Make it 1000000 to be sure.  There's a way to calculate the exact value but not
    # sure what it is yet
    min_utxo_value = cardano.get_min_utxo_value() + 1000000

    total_input_lovelace = 0
    for utxo in incoming_utxos:
        total_input_lovelace += utxo['amount']

    #fee
    fee = cardano.calculate_min_fee('transaction/mint_nft_external_draft_tx',
                                    len(incoming_utxos),
                                    1, 1)
    print("Fee = {} lovelace".format(fee))
    address_outputs[0]['amount'] = total_input_lovelace - min_utxo_value - fee
    address_outputs[1]['amount'] = min_utxo_value

    #final
    cardano.create_mint_nft_transaction_file(incoming_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             nft_metadata_file,
                                             1,
                                             'transaction/mint_nft_external_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/mint_nft_external_unsigned_tx',
                             minting_wallet.get_signing_key_file(),
                             'transaction/mint_nft_external_signed_tx')
    #submit
    cardano.submit_transaction('transaction/mint_nft_external_signed_tx')

def mint_next_nft_in_series(cardano: Cardano,
                            database: Database,
                            minting_wallet: Wallet,
                            policy_name: str,
                            input_utxo_hash: str,
                            nft_metadata_file: str) -> bool:
    """
    Mint the NFT defined in nft_metadata_file.

    @param nft_metadata_file Could contain a single asset or multiple assets
    """

    inputs = database.query_utxo_inputs(input_utxo_hash)
    if len(inputs) == 0:
        print("Waiting for DB SYNC.  Skipping...")
        return False

    input_address = inputs[0]['address']
    for inp in inputs:
        if inp['address'] != input_address:
            print("Received multiple inputs with different address.")
            print("Don't know what to do.  Skipping.")
            print('inputs: {}'.format(inputs))
            return False

    print('RX Payment From: {}'.format(input_address))

    destination = WalletExternal('customer',
                                 cardano.get_network(),
                                 input_address)
    token_name = None
    nft_metadata = Nft.parse_metadata_file(nft_metadata_file)
    policy_id = nft_metadata['policy-id']
    token_name = nft_metadata['token-names'][0]

    print("Minting NFT")
    mint_nft_external(cardano,
                      minting_wallet,
                      policy_name,
                      input_utxo_hash,
                      nft_metadata_file,
                      destination)

    # 1.  Query minting wallet until input utxo is gone.
    iterations = 0
    while cardano.contains_txhash(minting_wallet, input_utxo_hash):
        iterations += 1
        if iterations >= 100:
            print("Timeout waiting for txhash")
            break

        time.sleep(5)

    # 2.  Query destination wallet until a utxo with minted NFT appears
    iterations = 0
    while not cardano.contains_token(destination, '{}.{}'.format(policy_id,
                                                                 token_name)):
        iterations += 1
        if iterations >= 100:
            print("Timeout waiting for asset")
            break

        time.sleep(5)

    print('Transaction Complete')
    return True

def process_incoming_payments(cardano: Cardano,
                              database: Database,
                              minting_wallet: Wallet,
                              policy_name: str,
                              metadata_set_file: str,
                              prices: Dict[int, int]) -> None:
    """
    Listing for incoming payments and mint NFT to the address the payment came
    from.  NFTs are minted in the order defined in metadata_set_file and assumes
    that all NFTs have the same price.

    @param prices A dictionary to define the price for a single item or a bundle.
    """
    metadata_set = {}
    with open(metadata_set_file, "r") as file:
        metadata_set = json.loads(file.read())
        #random.shuffle(metadata_set['files'])

    if metadata_set == None:
        print('Series Metadata Set is None')
        return

    if len(metadata_set['files']) == 0:
        print('Series Metadata Set files list is empty')
        return

    while len(metadata_set['files']) > 0:
        (utxos, total_lovelace) = cardano.query_utxos(minting_wallet)
        for utxo in utxos:
            if utxo['amount'] in prices:
                num_nfts = prices[utxo['amount']]
                print("RX Purchase Request: {} NFTs".format(num_nfts))
                if len(metadata_set['files']) < num_nfts:
                    print('Not enough NFTs remaining')
                    print('Requested: {}, Have: {}.  Need to refund UTXO: {}'.format(num_nfts,
                                                                                     len(metadata_set['files'],
                                                                                     utxo['tx-hash'])))
                    return

                policy_id = cardano.get_policy_id(policy_name)
                input_utxo_hash = utxo['tx-hash']
                nft_metadata_files = []
                for i in range(0, num_nfts):
                    nft_metadata_files.append(metadata_set['files'].pop())
                merged_metadata_file = Nft.merge_metadata_files(policy_id,
                                                                nft_metadata_files)
                if not mint_next_nft_in_series(cardano,
                                               database,
                                               minting_wallet,
                                               policy_name,
                                               input_utxo_hash,
                                               merged_metadata_file):
                    print("Minting Failed")
                    for f in nft_metadata_files:
                        metadata_set['files'].append(f)

                with open(metadata_set_file, 'w') as file:
                    file.write(json.dumps(metadata_set, indent=4))

        if len(metadata_set['files']) == 0:
            print('ALL NFTs MINTED!!!!!')
            break

        print('Waiting for matching UTXO')
        time.sleep(30)

    print('!!!!!!!!!!!!!!!!!!!!!!!!')
    print('!!! MINTING COMPLETE !!!')
    print('!!!!!!!!!!!!!!!!!!!!!!!!')
