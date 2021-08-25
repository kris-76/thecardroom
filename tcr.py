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

import subprocess
import json
import os
from nft import Nft

from cardano import Cardano
from wallet import Wallet
from wallet import WalletExternal

DAYS_PER_YEAR = int(365)
MONTHS_PER_YEAR = int(12)
MINUTES_PER_HOUR = int(60)
HOURS_PER_DAY = int(24)
SECONDS_PER_MINUTE = int(60)

SECONDS_PER_HOUR = int(MINUTES_PER_HOUR * SECONDS_PER_MINUTE)
SECONDS_PER_DAY = int(HOURS_PER_DAY * SECONDS_PER_HOUR)
SECONDS_PER_MONTH = int((DAYS_PER_YEAR / MONTHS_PER_YEAR) * SECONDS_PER_DAY)
SECONDS_PER_YEAR = int(MONTHS_PER_YEAR * SECONDS_PER_MONTH)

def transfer_all_assets(cardano, from_wallet, to_wallet):
    (from_utxos, from_total_lovelace) = from_wallet.query_utxo()
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
    outputs = [{'address': to_wallet.get_payment_address(), 'amount': 0, 'assets': incoming_assets}]
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transaction/transfer_all_assets_draft_tx')


    # Calculate fee & update values 
    fee = cardano.calculate_min_fee('transaction/transfer_all_assets_draft_tx', len(from_utxos), len(outputs), 1)
    print("Fee = {} lovelace".format(fee))
    outputs[0]['amount'] = from_total_lovelace - fee

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transaction/transfer_all_assets_unsigned_tx')
   
    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_all_assets_unsigned_tx', from_wallet.get_signing_key_file(), 'transaction/transfer_all_assets_signed_tx')

    #submit
    cardano.submit_transaction('transaction/transfer_all_assets_signed_tx')

def transfer_ada(cardano, from_wallet, lovelace_amount, to_wallet):
    (from_utxos, from_total_lovelace) = from_wallet.query_utxo()
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
    outputs = [{'address': from_wallet.get_payment_address(), 'amount': 0, 'assets': incoming_assets},
               {'address': to_wallet.get_payment_address(), 'amount': 0, 'assets': {}}]
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transaction/transfer_ada_draft_tx')

    # Calculate fee & update values 
    fee = cardano.calculate_min_fee('transaction/transfer_ada_draft_tx', len(from_utxos), len(outputs), 1)
    print("Fee = {} lovelace".format(fee))
    outputs[0]['amount'] = from_total_lovelace - lovelace_amount - fee
    outputs[1]['amount'] = lovelace_amount

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transaction/transfer_ada_unsigned_tx')
   
    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_ada_unsigned_tx', from_wallet.get_signing_key_file(), 'transaction/transfer_ada_signed_tx')

    #submit
    cardano.submit_transaction('transaction/transfer_ada_signed_tx')

def transfer_nft(cardano, from_wallet, nft_assets, to_wallet):
    (from_utxos, from_total_lovelace) = from_wallet.query_utxo()
    # get all incoming assets from utxos
    incoming_assets = {}
    for utxo in from_utxos:
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
    outputs = [{'address': from_wallet.get_payment_address(), 'amount': 0, 'assets': incoming_assets},
               {'address': to_wallet.get_payment_address(), 'amount': 0, 'assets': nft_assets}]

    #draft
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transaction/transfer_nft_draft_tx')

    # https://github.com/input-output-hk/cardano-ledger-specs/blob/master/doc/explanations/min-utxo.rst
    # minUTxOValue is the minimum value if sending ADA only.  Since ADA plus a
    # custom NFT token is being sent the amount to send is larger.  500000 extra
    # seems to be ok.  Make it 1000000 to be sure.
    min_utxo_value = cardano.get_protocol_parameters()['minUTxOValue'] + 1000000

    # Calculate fee & update values 
    fee = cardano.calculate_min_fee('transaction/transfer_nft_draft_tx', len(from_utxos), len(outputs), 1)
    print("Fee = {} lovelace".format(fee))
    outputs[0]['amount'] = from_total_lovelace - min_utxo_value - fee
    outputs[1]['amount'] = min_utxo_value

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transaction/transfer_nft_unsigned_tx')
   
    # Sign the transaction
    cardano.sign_transaction('transaction/transfer_nft_unsigned_tx', from_wallet.get_signing_key_file(), 'transaction/transfer_nft_signed_tx')

    #submit
    cardano.submit_transaction('transaction/transfer_nft_signed_tx')

def burn_nft_internal(cardano, burning_wallet, policy_name, nft_token_name):
    (burning_utxos, burning_total_lovelace) = burning_wallet.query_utxo()

    incoming_assets = {}
    for utxo in burning_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    # The NFT burned will be removed from the output when the transaction is created
    address_outputs = [{'address': burning_wallet.get_payment_address(), 'amount': 0, 'assets': incoming_assets}]
    fee = 0
    # draft
    cardano.create_burn_nft_transaction_file(burning_utxos, address_outputs, fee, policy_name, nft_token_name, 1, 'transaction/burn_nft_internal_draft_tx')
    #fee
    fee = cardano.calculate_min_fee('transaction/burn_nft_internal_draft_tx', len(burning_utxos), 1, 1)
    print("Fee = {} lovelace".format(fee))
    address_outputs[0]['amount'] = burning_total_lovelace - fee
    #final
    cardano.create_burn_nft_transaction_file(burning_utxos, address_outputs, fee, policy_name, nft_token_name, 1, 'transaction/burn_nft_internal_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/burn_nft_internal_unsigned_tx', burning_wallet.get_signing_key_file(), 'transaction/burn_nft_internal_signed_tx')
    #submit
    cardano.submit_transaction('transaction/burn_nft_internal_signed_tx')

def mint_nft_internal(cardano, minting_wallet, policy_name, nft_token_name):
    (minting_utxos, minting_total_lovelace) = minting_wallet.query_utxo()

    incoming_assets = {}
    for utxo in minting_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    # The NFT minted will be added to the output when the transaction is created
    address_outputs = [{'address': minting_wallet.get_payment_address(), 'amount': 0, 'assets': incoming_assets}]
    fee = 0
    # draft
    cardano.create_mint_nft_transaction_file(minting_utxos, address_outputs, fee, policy_name, nft_token_name, 1, 'transaction/mint_nft_internal_draft_tx')
    #fee
    fee = cardano.calculate_min_fee('transaction/mint_nft_internal_draft_tx', len(minting_utxos), 1, 1)
    print("Fee = {} lovelace".format(fee))
    address_outputs[0]['amount'] = minting_total_lovelace - fee
    #final
    cardano.create_mint_nft_transaction_file(minting_utxos, address_outputs, fee, policy_name, nft_token_name, 1, 'transaction/mint_nft_internal_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/mint_nft_internal_unsigned_tx', minting_wallet.get_signing_key_file(), 'transaction/mint_nft_internal_signed_tx')
    #submit
    cardano.submit_transaction('transaction/mint_nft_internal_signed_tx')

def mint_nft_external(cardano, minting_wallet, policy_name, nft_token_name, destination_wallet):
    (minting_utxos, minting_total_lovelace) = minting_wallet.query_utxo()

    incoming_assets = {}
    for utxo in minting_utxos:
        for a in utxo['assets']:
            if a in incoming_assets:
                incoming_assets[a] += utxo['assets'][a]
            else:
                incoming_assets[a] = utxo['assets'][a]

    # The NFT minted will be added to the output when the transaction is created
    address_outputs = [{'address': minting_wallet.get_payment_address(), 'amount': 0, 'assets': incoming_assets},
                      {'address': destination_wallet.get_payment_address(), 'amount': 0, 'assets': {}}]

    # draft
    fee = 0
    cardano.create_mint_nft_transaction_file(minting_utxos, address_outputs, fee, policy_name, nft_token_name, 1, 'transaction/mint_nft_external_draft_tx')

    # https://github.com/input-output-hk/cardano-ledger-specs/blob/master/doc/explanations/min-utxo.rst
    # minUTxOValue is the minimum value if sending ADA only.  Since ADA plus a
    # custom NFT token is being sent the amount to send is larger.  500000 extra
    # seems to be ok.  Make it 1000000 to be sure.
    min_utxo_value = cardano.get_protocol_parameters()['minUTxOValue'] + 1000000

    #fee
    fee = cardano.calculate_min_fee('transaction/mint_nft_external_draft_tx', len(minting_utxos), 1, 1)
    print("Fee = {} lovelace".format(fee))
    address_outputs[0]['amount'] = minting_total_lovelace - min_utxo_value - fee
    address_outputs[1]['amount'] = min_utxo_value

    #final
    cardano.create_mint_nft_transaction_file(minting_utxos, address_outputs, fee, policy_name, nft_token_name, 1, 'transaction/mint_nft_external_unsigned_tx')
    #sign
    cardano.sign_transaction('transaction/mint_nft_external_unsigned_tx', minting_wallet.get_signing_key_file(), 'transaction/mint_nft_external_signed_tx')
    #submit
    cardano.submit_transaction('transaction/mint_nft_external_signed_tx')

