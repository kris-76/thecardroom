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
File: cardano.py
Author: Kris Henderson
"""

from typing import Dict, List, Tuple

import json
from command import Command
import copy
from nft import Nft
from wallet import Wallet
import logging

logger = logging.getLogger('cardano')

class Cardano:
    def __init__(self,
                 network:str,
                 protocol_parameters_file:str):
        self.network = network
        self.protocol_parameters_file = protocol_parameters_file
        self.protocol_parameters = {}

    def get_network(self) -> str:
        return self.network

    def query_tip(self) -> Dict:
        command = ['cardano-cli', 'query', 'tip']
        output = Command.run(command, self.network)
        tip = json.loads(output)
        return tip

    def query_protocol_parameters(self) -> Dict:
        self.protocol_parameters = {}

        command = ['cardano-cli', 'query', 'protocol-parameters', '--out-file', self.protocol_parameters_file]
        Command.run(command, self.network)

        with open(self.protocol_parameters_file, "r") as file:
            self.protocol_parameters = json.loads(file.read())
        return self.protocol_parameters

    def get_protocol_parameters_file(self) -> str:
        return self.protocol_parameters_file

    def get_protocol_parameters(self) -> Dict:
        return self.protocol_parameters

    def get_min_utxo_value(self) -> int:
        min_utxo_value = 1000000
        if self.get_protocol_parameters()['minUTxOValue'] != None:
            min_utxo_value = self.get_protocol_parameters()['minUTxOValue']

        return min_utxo_value

    def query_utxos(self,
                    wallet: Wallet,
                    addresses: List[str]=None) -> Tuple[List, int]:
        if addresses == None:
            addresses = list(dict.fromkeys([wallet.get_payment_address(0, delegated=False),
                                            wallet.get_payment_address(0, delegated=True),
                                            wallet.get_payment_address(1, delegated=False),
                                            wallet.get_payment_address(1, delegated=True)]))

        total_lovelace = 0
        utxos = []

        for payment_address in addresses:
            command = ['cardano-cli', 'query', 'utxo', '--address', payment_address]
            output = Command.run(command, self.network)

            # Calculate total lovelace of the UTXO(s) inside the wallet address
            utxo_table = output.splitlines()
            for x in range(2, len(utxo_table)):
                cells = utxo_table[x].split()
                assets = {}
                for x in range(4, len(cells), 3):
                    if cells[x] == '+':
                        if cells[x+1].isnumeric():
                            asset_amount = int(cells[x+1])
                            asset_name = cells[x+2]
                            assets[asset_name] = asset_amount

                tx_out_datum_hash = cells[len(cells) - 1]
                utxos.append({'tx-hash':cells[0], 'tx-ix':int(cells[1]), 'amount': int(cells[2]), 'assets': assets, 'tx-out-datum-hash': tx_out_datum_hash})
                total_lovelace +=  int(cells[2])

        return (utxos, total_lovelace)

    def query_utxos_dict(self,
                         wallet: Wallet,
                         addresses: List[str]=None) -> Dict:
        (utxos, lovelace) = self.query_utxos(wallet, addresses)
        output = {'lovelace': lovelace}
        for utxo in utxos:
            output[utxo['tx-hash']] = {'tx-ix':utxo['tx-ix'],
                                       'amount':utxo['amount'],
                                       'assets':utxo['assets'],
                                       'tx-out-datum-hash': utxo['tx-out-datum-hash']}

        return output

    def dump_utxos(self,
                   wallet: Wallet) -> None:
        print('{} UTXOS:'.format(wallet.get_name()))
        (utxos, lovelace) = self.query_utxos(wallet)
        for utxo in utxos:
            print("tx-hash = {}, tx-ix = {}, amount = {} lovelace".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
            for a in utxo['assets']:
                print('\t\t\t\t {} {}'.format(utxo['assets'][a], a))
            print("tx-out-datum-hash: {}".format(utxo['tx-out-datum-hash']))

        print("Total: {}".format(lovelace))

    def contains_txhash(self,
                        wallet,
                        txhash) -> bool:
        (utxos, lovelace) = self.query_utxos(wallet)
        for utxo in utxos:
            if utxo['tx-hash'] == txhash:
                return True

        return False

    def contains_token(self,
                       wallet,
                       full_token_name) -> bool:
        (utxos, lovelace) = self.query_utxos(wallet)
        for utxo in utxos:
            for a in utxo['assets']:
                if a == full_token_name:
                    return True

        return False

    def get_utxo(self,
                 wallet,
                 full_token_name) -> None:
        (utxos, lovelace) = self.query_utxos(wallet)
        for utxo in utxos:
            for a in utxo['assets']:
                if a == full_token_name:
                    return utxo

        return None

    def create_transfer_transaction_file(self,
                                         utxo_inputs,
                                         address_outputs,
                                         fee_amount,
                                         transaction_file) -> str:
        command = ['cardano-cli', 'transaction', 'build-raw']

        for utxo in utxo_inputs:
            command.append('--tx-in')
            command.append('{}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))


        for address in address_outputs:
            assets_string = ''
            for asset in address['assets']:
                if address['assets'][asset] > 0:
                    assets_string += '+{} {}'.format(address['assets'][asset], asset)

            # Note that if the amount is zero (or just too small) but there is a
            # valid asset in the output then this transaction will fail when
            # it is submitted
            if address['amount'] > 0 or len(assets_string) > 0:
                command.append('--tx-out')
                command.append('{}+{}{}'.format(address['address'], address['amount'], assets_string))

        command.extend(['--fee', '{}'.format(fee_amount),
                        '--out-file', transaction_file])

        output = Command.run(command, None)
        return output

    def create_mint_nft_transaction_file(self,
                                         utxo_inputs,
                                         address_outputs,
                                         fee_amount,
                                         policy_name,
                                         nft_metadata_file,
                                         transaction_file):
        nft_metadata = Nft.parse_metadata_file(nft_metadata_file)
        policy_id = nft_metadata['policy-id']
        token_names = nft_metadata['token-names']

        # address_outputs[0] = mint wallet address
        # address_outputs[1] = purchaser address

        if len(address_outputs) < 2:
            logger.error('Address outputs too short, len = {}'.format(len(address_outputs)))
            raise Exception('Address outputs too short, len = {}'.format(len(address_outputs)))

        mint = ''
        for token_name in token_names:
            if len(mint) > 0:
                mint += '+'

            mint += '1 {}.{}'.format(policy_id, token_name)
            # add the nft being minted to the output
            full_name = '{}.{}'.format(policy_id, token_name)
            address_outputs[1]['assets'][full_name] = 1

        invalid_hereafter = 0
        with open('policy/{}/{}.script'.format(self.network, policy_name), "r") as file:
            script = json.loads(file.read())
            for s in script['scripts']:
                if s['type'] == 'before':
                    invalid_hereafter = s['slot']

        command = ['cardano-cli', 'transaction', 'build-raw', '--fee', '{}'.format(fee_amount)]

        for utxo in utxo_inputs:
            command.append('--tx-in')
            command.append('{}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))

        for address in address_outputs:
            assets_string = ''
            for asset in address['assets']:
                assets_string += '+{} {}'.format(address['assets'][asset], asset)

            # Note that if the amount is zero (or just too small) but there is a
            # valid asset in the output then this transaction will fail when
            # it is submitted
            if address['amount'] > 0 or len(assets_string) > 0:
                command.append('--tx-out')
                command.append('{}+{}{}'.format(address['address'], address['amount'], assets_string))

        command.extend(['--mint={}'.format(mint),
                        '--minting-script-file', 'policy/{}/{}.script'.format(self.network, policy_name),
                        '--metadata-json-file', nft_metadata_file,
                        '--invalid-hereafter', '{}'.format(invalid_hereafter),
                        '--out-file', transaction_file])

        output = Command.run(command, None)
        return output

    # burning is just like minting except the value is negative
    def create_burn_nft_transaction_file(self,
                                         utxo_inputs: List,
                                         address_outputs: List[Dict],
                                         fee_amount: int,
                                         policy_name: str,
                                         token_name: str,
                                         nft_token_amount: int,
                                         transaction_file: str) -> str:
        # copy some stuff so it doesn't get modified to the caller
        address_outputs_cp = copy.deepcopy(address_outputs)

        policy_id = self.get_policy_id(policy_name)
        burn = '{} {}.{}'.format(-1*nft_token_amount, policy_id, token_name)

        # remove the nft being burned from the output
        full_name = '{}.{}'.format(policy_id, token_name)


        address_outputs_cp[len(address_outputs_cp)-1]['assets'][full_name] -= nft_token_amount

        invalid_hereafter = 0
        with open('policy/{}/{}.script'.format(self.network, policy_name), "r") as file:
            script = json.loads(file.read())
            for s in script['scripts']:
                if s['type'] == 'before':
                    invalid_hereafter = s['slot']

        command = ['cardano-cli', 'transaction', 'build-raw', '--fee', '{}'.format(fee_amount)]

        for utxo in utxo_inputs:
            command.append('--tx-in')
            command.append('{}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))

        for address in address_outputs_cp:
            assets_string = ''
            for asset in address['assets']:
                if address['assets'][asset] != 0:
                    assets_string += '+{} {}'.format(address['assets'][asset], asset)

            # Note that if the amount is zero (or just too small) but there is a
            # valid asset in the output then this transaction will fail when
            # it is submitted
            if address['amount'] > 0 or len(assets_string) > 0:
                command.append('--tx-out')
                command.append('{}+{}{}'.format(address['address'], address['amount'], assets_string))

        command.extend(['--mint={}'.format(burn),
                        '--minting-script-file', 'policy/{}/{}.script'.format(self.network, policy_name),
                        '--invalid-hereafter', '{}'.format(invalid_hereafter),
                        '--out-file', transaction_file])

        output = Command.run(command, None)
        return output

    def calculate_min_fee(self,
                          transaction_file: str,
                          tx_in_count: int,
                          tx_out_count: int,
                          witness_count: int) -> int:
        command = ['cardano-cli', 'transaction', 'calculate-min-fee', '--tx-body-file', transaction_file,
                   '--tx-in-count', str(tx_in_count), '--tx-out-count', str(tx_out_count),
                   '--witness-count', str(witness_count),
                   '--protocol-params-file', self.protocol_parameters_file]
        output = Command.run(command, self.network)
        cells = output.split()
        return int(cells[0])

    def sign_transaction(self,
                         unsigned_transaction_file: str,
                         signing_key_file: List[str],
                         signed_transaction_file: str) -> str:
        command = ['cardano-cli', 'transaction', 'sign', '--tx-body-file', unsigned_transaction_file]
        for file in signing_key_file:
            command.extend(['--signing-key-file', file])
        command.extend(['--out-file', signed_transaction_file])
        output = Command.run(command, self.network)
        return output

    def submit_transaction(self,
                           transaction_file: str) -> str:
        command = ['cardano-cli', 'transaction', 'submit', '--tx-file', transaction_file]
        output = Command.run(command, self.network)
        return output

    def create_new_policy_id(self,
                             before_slot: int,
                             policy_wallet: Wallet,
                             policy_name: str) -> str:
        # create new keys for the policy
        command = ['cardano-cli', 'address', 'key-gen',
                   '--verification-key-file', 'policy/{}/{}.vkey'.format(self.network, policy_name),
                   '--signing-key-file', 'policy/{}/{}.skey'.format(self.network, policy_name)]
        Command.run(command, None)

        # create signature hash from keys
        command = ['cardano-cli', 'address', 'key-hash',
                   '--payment-verification-key-file', policy_wallet.get_verification_key_file(0)]
        sig_key_hash = Command.run(command, None)

        # create script file requires sign by policy keys and only valid until specified slot
        with open('policy/{}/{}.script'.format(self.network, policy_name), 'w') as file:
            file.write('{\r\n')
            file.write('    \"type\":\"all\",\r\n')
            file.write('    \"scripts\":\r\n')
            file.write('    [\r\n')
            file.write('        {\r\n')
            file.write('            \"type\": \"before\",\r\n')
            file.write('            \"slot\": {}\r\n'.format(before_slot))
            file.write('        },\r\n')
            file.write('        {\r\n')
            file.write('            \"type\": \"sig\",\r\n')
            file.write('            \"keyHash\": \"{}\"\r\n'.format(sig_key_hash))
            file.write('        }\r\n')
            file.write('    ]\r\n')
            file.write('}\r\n')

        # generate the policy id
        command = ['cardano-cli', 'transaction', 'policyid',
                   '--script-file', 'policy/{}/{}.script'.format(self.network, policy_name)]
        output = Command.run(command, None)
        with open('policy/{}/{}.id'.format(self.network, policy_name), 'w') as file:
            file.write(output)

        return output

    def get_policy_id(self,
                      policy_name: str) -> str:
        policy_id = None

        try:
            with open('policy/{}/{}.id'.format(self.network, policy_name), 'r') as file:
                policy_id = file.read()
        except FileNotFoundError as e:
            policy_id = None

        return policy_id
