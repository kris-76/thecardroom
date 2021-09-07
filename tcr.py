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
import logging

DAYS_PER_YEAR = int(365)
MONTHS_PER_YEAR = int(12)
MINUTES_PER_HOUR = int(60)
HOURS_PER_DAY = int(24)
SECONDS_PER_MINUTE = int(60)

SECONDS_PER_HOUR = int(MINUTES_PER_HOUR * SECONDS_PER_MINUTE)
SECONDS_PER_DAY = int(HOURS_PER_DAY * SECONDS_PER_HOUR)
SECONDS_PER_MONTH = int((DAYS_PER_YEAR / MONTHS_PER_YEAR) * SECONDS_PER_DAY)
SECONDS_PER_YEAR = int(MONTHS_PER_YEAR * SECONDS_PER_MONTH)

logger = logging.getLogger('tcr')

def transfer_all_assets(cardano: Cardano,
                        from_wallet: Wallet,
                        to_wallet: Wallet) -> None:
    """
    Transfer all assets (lovelace and other tokens) from one wallet to another.
    """

    logger.debug('Transfer All Assets, from: {}, to: {}'.format(from_wallet.get_name(), to_wallet.get_name()))

    (from_utxos, from_total_lovelace) = cardano.query_utxos(from_wallet)
    # get all incoming assets from utxos
    incoming_assets = {}
    for utxo in from_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    logger.debug('Transfer All Assets, From Wallet({}) = {} lovelace'.format(from_wallet.get_name(), from_total_lovelace))

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
    logger.debug('Transfer All Assets, Fee = {} lovelace'.format(fee))

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

    logger.debug('Transfer ADA, lovelace: {} from: {}, to: {}'.format(lovelace_amount, from_wallet.get_name(), to_wallet.get_name()))

    (from_utxos, from_total_lovelace) = cardano.query_utxos(from_wallet)
    # get all incoming assets from utxos
    incoming_assets = {}
    for utxo in from_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    logger.debug('Transfer ADA, From Wallet({}) = {} lovelace'.format(from_wallet.get_name(), from_total_lovelace))

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

    logger.debug('Transfer ADA, Fee = {} lovelace'.format(fee))

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

    logger.debug('Transfer NFT, from: {}, to: {}'.format(from_wallet.get_name(), to_wallet.get_name()))

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

    logger.debug('Transfer NFT, From Wallet({}) = {} lovelace'.format(from_wallet.get_name(), from_total_lovelace))

    # subtract outgoing assets
    for a in nft_assets:
        logger.debug('NFT: {} {}'.format(nft_assets[a], a))
        incoming_assets[a] -= nft_assets[a]
        if incoming_assets[a] < 0:
            raise Exception('Asset value less than zero.')

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

    outputs[0]['amount'] = from_total_lovelace - min_utxo_value - fee
    outputs[1]['amount'] = min_utxo_value

    logger.debug('Transfer NFT, Fee = {} lovelace'.format(fee))
    logger.debug('Transfer NFT, ADA min tx = {} lovelace'.format(min_utxo_value))

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

    logger.debug('Mint NFT External, source: {}, input txhash: {}, policy: {}'.format(minting_wallet.get_name(), input_txhash, policy_name))
    logger.debug('Mint NFT External, NFT: {}, destination: {}'.format(nft_metadata_file, destination_wallet.get_payment_address()))

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

    logger.debug('Mint NFT External, Mint Wallet({}) = {} lovelace'.format(minting_wallet.get_name(), minting_lovelace))

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
    address_outputs[0]['amount'] = total_input_lovelace - min_utxo_value - fee
    address_outputs[1]['amount'] = min_utxo_value

    logger.debug('Mint NFT External, Fee = {} lovelace'.format(fee))
    logger.debug('Mint NFT External, ADA min tx = {} lovelace'.format(min_utxo_value))

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

    logger.debug('Mint Next Series NFT, source: {}, input txhash: {}, policy: {}'.format(minting_wallet.get_name(), input_utxo_hash, policy_name))
    logger.debug('Mint Next Series NFT, NFT: {}'.format(nft_metadata_file))

    inputs = database.query_utxo_inputs(input_utxo_hash)
    if len(inputs) == 0:
        logger.warning('Mint Next Series NFT, No UTXO Inputs - Waiting for DB SYNC.  Skip for now.')
        return False

    input_address = inputs[0]['address']
    for inp in inputs:
        if inp['address'] != input_address:
            logger.warning("Mint Next Series NFT, Received multiple inputs with different address.")
            logger.warning("Mint Next Series NFT, Don't know what to do.  Skipping.")
            logger.warning('Mint Next Series NFT, inputs: {}'.format(inputs))
            return False

    logger.info('Mint Next Series NFT, RX Payment From: {}'.format(input_address))

    destination = WalletExternal('customer',
                                 cardano.get_network(),
                                 input_address)
    token_name = None
    nft_metadata = Nft.parse_metadata_file(nft_metadata_file)
    policy_id = nft_metadata['policy-id']
    token_name = nft_metadata['token-names'][0]

    logger.info('Mint Next Series NFT, Minting NFT to external wallet')
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
            logger.warning('Mint Next Series NFT, Timeout waiting for txhash')
            break

        time.sleep(6)

    # 2.  Query destination wallet until a utxo with minted NFT appears
    iterations = 0
    while not cardano.contains_token(destination, '{}.{}'.format(policy_id,
                                                                 token_name)):
        iterations += 1
        if iterations >= 100:
            logger.warning('Mint Next Series NFT, Timeout waiting for asset')
            break

        time.sleep(6)

    utxo = cardano.get_utxo(destination, '{}.{}'.format(policy_id, token_name))
    logger.info('TX HASH: {}'.format(utxo['tx-hash']))
    for a in utxo['assets']:
        logger.info('\t{} {}'.format(utxo['assets'][a], a))

    logger.info('Mint Next Series NFT, Transaction Complete!  {}'.format(utxo['tx-hash']))

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

    logger = logging.getLogger('tcr')

    logger.info('Processing Payments')

    metadata_set = {}
    with open(metadata_set_file, "r") as file:
        metadata_set = json.loads(file.read())

    if metadata_set == None:
        logger.warning('Series Metadata Set is None')
        return

    if len(metadata_set['files']) == 0:
        logger.warning('Series Metadata Set File List is Empty')
        return

    while len(metadata_set['files']) > 0:
        (utxos, total_lovelace) = cardano.query_utxos(minting_wallet)
        for utxo in utxos:
            if utxo['amount'] in prices:
                num_nfts = prices[utxo['amount']]
                logger.info('Processing Payments, RX {} lovelace for {} NFTS'.format(utxo['amount'], num_nfts))
                if len(metadata_set['files']) < num_nfts:
                    logger.error('Processing Payments, Not enough NFTs remaining')
                    logger.error('Processing Payments, Requested: {}, Have: {}.  Need to refund UTXO: {}'.format(num_nfts,
                                                                                                                 len(metadata_set['files']),
                                                                                                                 utxo['tx-hash']))
                    return

                policy_id = cardano.get_policy_id(policy_name)
                input_utxo_hash = utxo['tx-hash']
                nft_metadata_files = []
                for i in range(0, num_nfts):
                    mdfile = metadata_set['files'].pop()
                    nft_metadata_files.append(mdfile)
                    logger.debug('Processing Payments, merging NFT metadata: {}'.format(mdfile))

                merged_metadata_file = Nft.merge_metadata_files(policy_id,
                                                                nft_metadata_files)
                logger.debug('Processing Payments, Merged NFT Metadata File: {}'.format(merged_metadata_file))
                if not mint_next_nft_in_series(cardano,
                                               database,
                                               minting_wallet,
                                               policy_name,
                                               input_utxo_hash,
                                               merged_metadata_file):
                    logger.error('Processing Payments, Minting Failed')
                    for f in nft_metadata_files:
                        metadata_set['files'].append(f)

                with open(metadata_set_file, 'w') as file:
                    file.write(json.dumps(metadata_set, indent=4))

        if len(metadata_set['files']) == 0:
            logger.info('Processing Payments, ALL NFTs MINTED!!!!!')
            break

        logger.debug('Processing Payments, Waiting for matching UTXO')
        time.sleep(30)

    logger.info('Processing Payments, !!!!!!!!!!!!!!!!!!!!!!!!')
    logger.info('Processing Payments, !!! MINTING COMPLETE !!!')
    logger.info('Processing Payments, !!!!!!!!!!!!!!!!!!!!!!!!')
