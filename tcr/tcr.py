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
from typing import List

from tcr.nft import Nft
from tcr.cardano import Cardano
from tcr.wallet import Wallet
from tcr.wallet import WalletExternal
from tcr.database import Database
from tcr.metadata_list import MetadataList

import json
import time
import logging
from tcr.sales import Sales

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

    logger.debug('Transfer All Assets, from: {}, to: {}'.format(from_wallet.get_name(), to_wallet.get_payment_address()))

    (from_utxos, from_total_lovelace) = cardano.query_utxos(from_wallet)

    if len(from_utxos) == 0:
        logger.error('No Input UTXOs')
        return None

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
                             [from_wallet.get_signing_key_file(0), from_wallet.get_signing_key_file(1)],
                             'transaction/transfer_all_assets_signed_tx')

    #submit
    tx_id = cardano.submit_transaction('transaction/transfer_all_assets_signed_tx')

    return tx_id

def transfer_utxo_ada(cardano: Cardano,
                      from_wallet: Wallet,
                      utxo: Dict,
                      to_wallet: Wallet) -> None:
    """
    Transfer all ADA in the specified UTXO.  Gas fee comes from UTXO.
    """

    logger.debug('Transfer UTXO ADA, from: {}, to: {}'.format(from_wallet.get_name(), to_wallet.get_payment_address()))
    if len(utxo['assets']) > 0:
        logger.warning("Transfer UTXO ADA, UTXO contains other assets.  Skipping TX.")
        return
    logger.debug('Transfer UTXO ADA, UTXO: {}, lovelace: {}'.format(utxo['tx-hash'], utxo['amount']))

    # Draft transaction for fee calculation
    outputs = [{'address': to_wallet.get_payment_address(),
                'amount': 1,
                'assets': {}}]
    fee = 0
    cardano.create_transfer_transaction_file([utxo],
                                             outputs,
                                             fee,
                                             'transaction/transfer_utxo_ada_draft_tx')

    # Calculate fee & update values
    fee = cardano.calculate_min_fee('transaction/transfer_utxo_ada_draft_tx',
                                    1, len(outputs), 1)
    outputs[0]['amount'] = utxo['amount'] - fee
    logger.debug('Transfer UTXO ADA, Fee = {} lovelace'.format(fee))
    logger.debug('Transfer UTXO ADA, Lovelace = {} lovelace'.format(outputs[0]['amount']))

    # Final unsigned transaction
    cardano.create_transfer_transaction_file([utxo],
                                             outputs,
                                             fee,
                                             'transaction/transfer_utxo_ada_unsigned_tx')

    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_utxo_ada_unsigned_tx',
                             [from_wallet.get_signing_key_file(0), from_wallet.get_signing_key_file(1)],
                             'transaction/transfer_utxo_ada_signed_tx')

    # submit
    tx_id = cardano.submit_transaction('transaction/transfer_utxo_ada_signed_tx')

    return (tx_id, fee, utxo['amount'] - fee)

def transfer_ada(cardano: Cardano,
                 from_wallet: Wallet,
                 lovelace_amount: int,
                 to_wallet: Wallet) -> None:
    """
    Transfer lovelace from one wallet to another.
    """

    logger.debug('Transfer ADA, lovelace: {} from: {}, to: {}'.format(lovelace_amount, from_wallet.get_name(), to_wallet.get_payment_address()))

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
                                    len(outputs),
                                    1)
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
                             [from_wallet.get_signing_key_file(0), from_wallet.get_signing_key_file(1)],
                             'transaction/transfer_ada_signed_tx')

    #submit
    tx_id = cardano.submit_transaction('transaction/transfer_ada_signed_tx')

    return tx_id

def transfer_nft(cardano: Cardano,
                 from_wallet: Wallet,
                 nft_assets: Dict[str, int],
                 to_wallet: Wallet) -> None:
    """
    Transfer an NFT from one wallet to another.

    Also transfers the minimum lovelace amount defined by the network parameters
    plus 1000000.  As of today, that is 2 ADA.
    """

    logger.debug('Transfer NFT, from: {}, to: {}'.format(from_wallet.get_name(), to_wallet.get_payment_address()))

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
                             [from_wallet.get_signing_key_file(0), from_wallet.get_signing_key_file(1)],
                             'transaction/transfer_nft_signed_tx')

    #submit
    tx_id = cardano.submit_transaction('transaction/transfer_nft_signed_tx')

    return tx_id

def burn_nft_internal(cardano: Cardano,
                      burning_wallet: Wallet,
                      policy_name: str,
                      input_utxos: List[Dict],
                      token_names: List[str],
                      token_amount: int = 1) -> None:
    """
    Burn one NFT.
    """

    incoming_assets = {}
    input_total_lovelace = 0
    for utxo in input_utxos:
        input_total_lovelace += utxo['amount']
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
    cardano.create_burn_nft_transaction_file(input_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             token_names,
                                             token_amount,
                                             'transaction/burn_nft_internal_draft_tx')
    #fee
    fee = cardano.calculate_min_fee('transaction/burn_nft_internal_draft_tx',
                                    len(input_utxos),
                                    1,
                                    1)
    address_outputs[0]['amount'] = input_total_lovelace - fee
    #final
    cardano.create_burn_nft_transaction_file(input_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             token_names,
                                             token_amount,
                                             'transaction/burn_nft_internal_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/burn_nft_internal_unsigned_tx',
                             [burning_wallet.get_signing_key_file(0),
                              burning_wallet.get_signing_key_file(1)],
                             'transaction/burn_nft_internal_signed_tx')
    #submit
    tx_id = cardano.submit_transaction('transaction/burn_nft_internal_signed_tx')

    return tx_id

def verify_unique_nfts(cardano: Cardano,
                       database: Database,
                       policy_name: str,
                       nft_metadata_file: str) -> bool:
    # Make sure we're not about to mint multiple of the same token
    # Make sure the token we're about to mint hasn't already been minted
    nft_metadata = Nft.parse_metadata_file(nft_metadata_file)
    policy_id = nft_metadata['policy-id']

    if policy_id != cardano.get_policy_id(policy_name):
        logger.error("Policy ID mismatch")
        return False

    token_names = nft_metadata['token-names']
    minted_nfts = database.query_mint_transactions(policy_id)

    for name in token_names:
        if token_names.count(name) > 1:
            logger.error('Minting multiple of the same token')
            return False

        if name in minted_nfts:
            logger.error('Token already minted!')
            return False

    return True

def mint_nft_external(cardano: Cardano,
                      database: Database,
                      minting_wallet: Wallet,
                      policy_name: str,
                      input_utxos: List,
                      nft_metadata_file: str,
                      sales: Sales) -> bool:
    """
    Mint an NFT to a different wallet.

    input_utxos is a list of dictionaries.  Each object in the list looks like:
    {"utxo": Dict, "count": N}
    "utxo" is minting "N" NFTs.  The sum must add up to the number in nft_metadata_file
    Each utxo is assumed to contain 0 other assets.
    The destination address will be queried for each input utxo

    Also transfers the minimum lovelace amount as defined by the network protocol
    parameters plus 1000000.  Currently 2 ADA.
    """

    if not verify_unique_nfts(cardano, database, policy_name, nft_metadata_file):
        logger.error("NFT Uniqueness Violation found.")
        raise Exception('NFT Uniqueness Violation')

    # The NFT minted will be added to the output when the transaction is created
    address_outputs = [{
                           'address': minting_wallet.get_payment_address(0),
                           'amount': 1,
                           'assets': {}
                       }]

    for item in input_utxos:
        inputs = database.query_utxo_inputs(item['utxo']['tx-hash'])
        if len(inputs) == 0:
            logger.warning('Mint NFT External, No UTXO Inputs - Waiting for DB SYNC.  Skip for now.')
            return False

        # There can be different addresses in the inputs.  Arbitrarily pick the
        # first one.  These should all map to the same stake address
        address_outputs.append({
                                   'address': inputs[0]['address'],
                                   'amount': 1,
                                   'assets': {}
                               })
        sales.set_input_address(item['utxo']['tx-hash'], item['utxo']['tx-ix'], inputs[0]['address'])

    # tip address
    address_outputs.append({
                                'address': {'mainnet': 'addr1q88q8fmttd9lt4pgtc3g778w74jxsk9r7q2mmt5lhpyw3sl8mam03vp3qc8k8lmgsdlf6p43xcmcmp6jgx2y6w62nszq070rcs',
                                            'testnet': 'addr_test1vzwyk8nwfh5esy09z79nzyxe69y8u5wdx60vgxsnu0w0q7cxqx50m'}[cardano.get_network()],
                                'amount': 1,
                                'assets': {}
                            })

    # draft
    fee = 0
    cardano.create_mint_nft_transaction_file(input_utxos,
                                             address_outputs,
                                             fee,
                                             policy_name,
                                             nft_metadata_file,
                                             'transaction/mint_nft_external_draft_tx')

    # https://github.com/input-output-hk/cardano-ledger-specs/blob/master/doc/explanations/min-utxo.rst
    cardano.calculate_min_required_utxo_mint(input_utxos,
                                             address_outputs,
                                             nft_metadata_file)

    total_input_lovelace = 0
    for item in input_utxos:
        total_input_lovelace += item['utxo']['amount']

    logger.debug("Mint NFT External, total payment received: {} ADA".format(total_input_lovelace / 1000000))

    #fee
    fee = cardano.calculate_min_fee('transaction/mint_nft_external_draft_tx',
                                    len(input_utxos),
                                    len(address_outputs),
                                    1)

    # update output amounts
    address_outputs[0]['amount'] = total_input_lovelace - fee # the project keeps

    for i in range(0, len(input_utxos)):
        # the first UTXO corresponds to the second address and so on
        out_min_ada = address_outputs[i+1]['min-required-utxo']
        out_min_ada = int(out_min_ada + input_utxos[i]['refund'])
        address_outputs[0]['amount'] = address_outputs[0]['amount'] - out_min_ada # remove from the project
        address_outputs[i+1]['amount'] = out_min_ada             # give to minter for tx min ADA requirement
        sales.set_tx_ada(input_utxos[i]['utxo']['tx-hash'], input_utxos[i]['utxo']['tx-ix'], out_min_ada)

    if len(address_outputs) == len(input_utxos) + 2:
        address_outputs[-1]['amount'] = cardano.get_min_utxo_value()  # thank the dev
        address_outputs[0]['amount'] -= address_outputs[-1]['amount'] # remove from the project

    for output in address_outputs:
        logger.debug('Mint NFT External, TX ADA Amount {} = {}'.format(output['address'], output['amount']))

    # If our profit is less than the minimum required then just send everything back to the
    # purchaser.  This represents a special case where we are allowing someone
    # to mint our NFTs only for the network gas fee.  They will send 2.5 ADA and
    # receive about 2.3 back.
    if address_outputs[0]['amount'] < cardano.get_min_utxo_value():
        logger.debug('Mint NFT External, adjust outputs')
        address_outputs[1]['amount'] = address_outputs[1]['amount'] + address_outputs[0]['amount']
        address_outputs[0]['amount'] = 0
        sales.set_tx_ada(input_utxos[0]['utxo']['tx-hash'], input_utxos[0]['utxo']['tx-ix'], address_outputs[1]['amount'])
        logger.debug('Mint NFT External, adjusted output[0] {} = {}'.format(address_outputs[0]['address'], address_outputs[0]['amount']))
        logger.debug('Mint NFT External, adjusted output[1] {} = {}'.format(address_outputs[1]['address'], address_outputs[1]['amount']))

    logger.debug('Mint NFT External, Fee = {} lovelace'.format(fee))

    #final
    (output, mint_map) = cardano.create_mint_nft_transaction_file(input_utxos,
                                                                  address_outputs,
                                                                  fee,
                                                                  policy_name,
                                                                  nft_metadata_file,
                                                                  'transaction/mint_nft_external_unsigned_tx')
    for item in mint_map:
        hash = item.split('#')[0]
        ix = int(item.split('#')[1])
        sales.set_tokens_minted(hash, ix, mint_map[item]['tokens'])

    #sign
    cardano.sign_transaction('transaction/mint_nft_external_unsigned_tx',
                             [minting_wallet.get_signing_key_file(0), minting_wallet.get_signing_key_file(1)],
                             'transaction/mint_nft_external_signed_tx')
    #submit
    tx_id = cardano.submit_transaction('transaction/mint_nft_external_signed_tx')

    return tx_id

def batch_mint_next_nft_in_series(cardano: Cardano,
                                  database: Database,
                                  minting_wallet: Wallet,
                                  policy_name: str,
                                  input_utxos: List,
                                  nft_metadata_file: str,
                                  sales: Sales) -> bool:
    """
    Mint the NFT defined in nft_metadata_file.

    @param nft_metadata_file Could contain a single asset or multiple assets
    """

    logger.debug('Mint Next Series NFT, merged nft metadata: {}'.format(nft_metadata_file))
    for item in input_utxos:
        logger.debug('Mint Next Series NFT, {} / {}, {} NFTs, input: {}#{}'.format(minting_wallet.get_name(), policy_name, item['count'], item['utxo']['tx-hash'], item['utxo']['tx-ix']))
        sales.add_utxo(item['utxo']['tx-hash'], item['utxo']['tx-ix'], item['utxo']['amount'], item['count'])

    nft_metadata = Nft.parse_metadata_file(nft_metadata_file)

    logger.info('Mint Next Series NFT, Mint NFTs: {}'.format(nft_metadata['token-names']))
    tx_id = mint_nft_external(cardano,
                              database,
                              minting_wallet,
                              policy_name,
                              input_utxos,
                              nft_metadata_file,
                              sales)

    if tx_id != None:
        # Set the output txid to mark the transaction successful
        for item in input_utxos:
            sales.set_output_txid(item['utxo']['tx-hash'], item['utxo']['tx-ix'], tx_id)
    else:
        # delete the utxo so the main payment processor will try again
        for item in input_utxos:
            sales.remove_utxo(item['utxo']['tx-hash'], item['utxo']['tx-ix'])

#    # wait for the transaction to complete by seeing the output tx id show up
#    # in our wallet
#    iterations = 0
#    while not cardano.contains_txhash(minting_wallet, tx_id):
#        iterations += 1
#        if iterations >= 100:
#            logger.warning('Mint Next Series NFT, Timeout waiting for tx id')
#            sales.set_timeout(True)
#            break
#
#        time.sleep(10)
#
#    logger.info('Mint Next Series NFT, Transaction Complete!')

    return True

def refund_payment(cardano: Cardano,
                   database: Database,
                   wallet: Wallet,
                   utxo: Dict,
                   sales: Sales) -> None:
    logger.debug('Refund Payment, from: {} / UTXO: {}'.format(wallet.get_name(), utxo['tx-hash']))
    logger.debug('Refund Payment, amount: {} lovelace'.format(wallet.get_name(), utxo['amount']))
    sales.add_utxo(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], 0)

    inputs = database.query_utxo_inputs(utxo['tx-hash'])
    if len(inputs) == 0:
        logger.warning('Refund Payment, No UTXO Inputs - Waiting for DB SYNC.  Skip for now.')
        sales.remove_utxo(utxo['tx-hash'], utxo['tx-ix'])
        return False

    # There can be different addresses in the inputs but they should be from the
    # same wallet, Arbitrarily pick the first one.
    input_address = inputs[0]['address']
    sales.set_input_address(utxo['tx-hash'], utxo['tx-ix'], input_address)
    destination = WalletExternal('customer',
                                 cardano.get_network(),
                                 input_address)

    (tx_id, fee, amount) = transfer_utxo_ada(cardano, wallet, utxo, destination)
    sales.set_output_txid(utxo['tx-hash'], utxo['tx-ix'], tx_id)
    sales.set_tx_ada(utxo['tx-hash'], utxo['tx-ix'], amount)
    sales.set_refund(utxo['tx-hash'], utxo['tx-ix'], fee, amount)
    sales.commit()

    return True

def process_incoming_payments(cardano: Cardano,
                              database: Database,
                              minting_wallet: Wallet,
                              policy_name: str,
                              drop_name: str,
                              metadata_set_file: str,
                              prices: Dict[int, int],
                              max_per_tx: int) -> None:
    """
    Listing for incoming payments and mint NFT to the address the payment came
    from.  NFTs are minted in the order defined in metadata_set_file and assumes
    that all NFTs have the same price.

    @param prices A dictionary to define the price for a single item or a bundle.
    """

    logger.info('Monitor Incoming Payments on: {}'.format(minting_wallet.get_payment_address()))
    sales = Sales(cardano.get_network(), drop_name)

    nft_metadata = MetadataList(metadata_set_file)
    logger.info('process_incoming_payments, NFTs Remaining: {}'.format(nft_metadata.get_remaining()))

    while True:
        time.sleep(1)
        (utxos, total_lovelace) = cardano.query_utxos(minting_wallet, [minting_wallet.get_payment_address()])
        utxos = cardano.query_utxos_time(database, utxos)
        utxos.sort(key=lambda item : item['slot-no'])

        matching_utxos = 0
        for utxo in utxos:
            if utxo['amount'] in prices:
                matching_utxos += 1

        if matching_utxos == 0:
            logger.debug('process_incoming_payments, Waiting for matching UTXO')
            time.sleep(30)
            continue

        if nft_metadata.get_remaining() > 0:
            if len(utxos) > 0:
                # There are NFTs available.  So go find a UTXO that NFTs can be minted to.
                # Collect incoming utxos that match a payment and batch them together for processing
                input_utxos = []
                nfts_to_mint = 0

                # search for UTXOs that the full requested amount can be fulfilled
                for utxo in utxos:
                    if sales.contains(utxo['tx-hash'], utxo['tx-ix']):
                        # If already processed this UTXO then skip it.
                        continue

                    logger.info('RX UTXO {}: {} lovelace'.format(utxo['tx-hash'], utxo['amount']))
                    if utxo['amount'] in prices:
                        num_nfts = prices[utxo['amount']]
                        logger.info('Request {} NFTs'.format(num_nfts))
                        if num_nfts + nfts_to_mint <= nft_metadata.get_remaining() and num_nfts + nfts_to_mint <= max_per_tx:
                            input_utxos.append({'utxo': utxo, 'count': num_nfts, 'refund': 0})
                            logger.debug('Queue For Mint, UTXO {} = {} NFTs, refund: {}'.format(utxo['tx-hash'], num_nfts, 0))
                            nfts_to_mint += num_nfts
                        else:
                            # reached the maximum amount that can be processed.  Check to see if
                            # a partial amount can be granted
                            if nfts_to_mint == 0:
                                if num_nfts > nft_metadata.get_remaining():
                                    price_per_nft = utxo['amount'] / num_nfts
                                    refund_nfts = num_nfts - nft_metadata.get_remaining()
                                    refund_price = int(refund_nfts * price_per_nft)
                                    num_nfts = nft_metadata.get_remaining()
                                    input_utxos.append({'utxo': utxo, 'count': num_nfts, 'refund': refund_price})
                                    nfts_to_mint += num_nfts
                                    logger.debug('Queue For Mint, UTXO {} = {} NFTs, refund: {}'.format(utxo['tx-hash'], num_nfts, refund_price))
                                else:
                                    logger.error("Configuration error: max_per_tx < num requested for price")
                                    raise Exception("Configuration error: max_per_tx < num requested for price")

                            break

                # by now there should be something to mint.  If not then that means a
                # UTXO was received that did not have a match to any payment price.
                if nfts_to_mint > 0:
                    logger.debug('Mint {} NFTs for {} queued UTXOs'.format(nfts_to_mint, len(input_utxos)))
                    # Mint the NFTs requested
                    nft_metadata_files = []
                    for i in range(0, nfts_to_mint):
                        mdfile = nft_metadata.peek_next_file()
                        nft_metadata_files.append(mdfile)
                        logger.debug('Merging NFT metadata: {}'.format(mdfile))

                    policy_id = cardano.get_policy_id(policy_name)
                    merged_metadata_file = Nft.merge_metadata_files(policy_id,
                                                                    nft_metadata_files)

                    if not batch_mint_next_nft_in_series(cardano,
                                                         database,
                                                         minting_wallet,
                                                         policy_name,
                                                         input_utxos,
                                                         merged_metadata_file,
                                                         sales):
                        nft_metadata.revert()
                        logger.error('process_incoming_payments, Fail to mint')
                    else:
                        nft_metadata.commit()
                        logger.info('Mint complete')
                        logger.info('Monitor Incoming Payments on: {}'.format(minting_wallet.get_payment_address()))
                        logger.info('process_incoming_payments, NFTs Remaining: {}'.format(nft_metadata.get_remaining()))
                    sales.commit()
                else:
                    # The UTXO is being processed
                    pass
        else:
            # No NFTs available.  Any UTXO that matches a payment amount will be
            # refunded
            input_utxos = []

            # Copy the UTXOs that match a payment amount
            for utxo in utxos:
                if sales.contains(utxo['tx-hash'], utxo['tx-ix']):
                    # If already processed this UTXO then skip it.
                    continue

                if utxo['amount'] in prices:
                    logger.debug('Queue For Refund, UTXO {} = {} NFTs, refund: {}'.format(utxo['tx-hash'], 0, utxo['amount']))
                    input_utxos.append({'utxo': utxo, 'count': 0})

            # Give the refund
            for item in input_utxos:
                logger.info("Refund: {} = {}".format(item['utxo']['tx-hash'], item['utxo']['amount']))
                if not refund_payment(cardano, database, minting_wallet, item['utxo'], sales):
                    logger.error('processing_incoming_payments, Fail to refund')
                else:
                    logger.info('processing_incoming_payments, Refund complete.')
            time.sleep(30)


    logger.info('!!!!!!!!!!!!!!!!!!!!!!!!')
    logger.info('!!! MINTING COMPLETE !!!')
    logger.info('!!!!!!!!!!!!!!!!!!!!!!!!')
