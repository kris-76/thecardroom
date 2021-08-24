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
File: wallet.py
Description: Utility functions for interacting with cardano-wallet and cardano-cli
Author: Kris Henderson
"""

# https://github.com/input-output-hk/cardano-addresses

import subprocess
import json
import os

networks = {
    'testnet': ['--testnet-magic', '1097911063'],
    'mainnet': ['--mainnet']
}

node_socket_env = {
    'testnet': 'TESTNET_CARDANO_NODE_SOCKET_PATH',
    'mainnet': 'MAINNET_CARDANO_NODE_SOCKET_PATH',
    'active': 'CARDANO_NODE_SOCKET_PATH'
}

def write_to_file(filename, data):
    with open(filename, 'w') as file:
        file.write(data)

def print_command(command):
    print('Command: ', end='')
    for c in command:
        if ' ' not in c:
            print('{} '.format(c), end='')
        else:
            print('\"{}\" '.format(c), end='')
    print('')

def run_command(command, network, input=None):
    envvars = os.environ

    if network != None:
        envvars[node_socket_env['active']] = os.environ[node_socket_env[network]]
        command.extend(networks[network])

    print_command(command)
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, input=input, env=envvars)
    except subprocess.CalledProcessError as e:
        print('{} ERROR {}'.format(command[0], e.returncode))
        print('output: {}'.format(e.output))
        print('stdout: {}'.format(e.stdout))
        print('stderr: {}'.format(e.stderr))
        raise e

    # print("Command stdout: {}".format(completed.stdout.strip('\r\n')))
    return completed.stdout.strip('\r\n')

class Wallet:
    def __init__(self, name, cardano):
        self.name = name
        self.cardano = cardano
        self.mnemonic_phrase_file = '{}.mnemonic'.format(name)
        self.root_extended_private_key_file = '{}_root.xprv'.format(name)
        self.extended_private_key_file = '{}_key.xsk'.format(name)
        self.signing_key_file = '{}_key.skey'.format(name)
        self.verification_key_file = '{}_key.vkey'.format(name)
        self.payment_address_file = '{}_payment.addr'.format(name)

    def exists(self):
        return os.path.exists(self.signing_key_file) and os.path.exists(self.verification_key_file) and os.path.exists(self.payment_address_file)

    def create_new_wallet(self):
        mnemonic = Wallet.create_mnemonic_phrase()
        write_to_file("{}.mnemonic".format(self.name), mnemonic)
        self.generate_key_files(mnemonic)
        self.create_address_file()
        return self.exists()

    def get_payment_address(self):
        payment_address = None

        with open(self.payment_address_file, 'r') as file:
            payment_address = file.read()

        return payment_address

    def get_signing_key_file(self):
        return self.signing_key_file

    def get_verification_key_file(self):
        self.verification_key_file

    # Create a mnemonic phrase that can be used with cardano-wallet, yoroi, dadaelus, etc....
    @staticmethod
    def create_mnemonic_phrase():
        command = ['cardano-wallet', 'recovery-phrase', 'generate']
        output = run_command(command, network=None)
        return output

    @staticmethod
    def create_root_extended_private_key(mnemonic):
        command = ['cardano-address', 'key', 'from-recovery-phrase', 'Shelley']
        output = run_command(command, input=mnemonic, network=None)
        return output
    
    # Uses derivation path:
    #  - 1852H: purpose = not sure...
    #  - 1815H: coin-type = Cardano ADA
    #  - 0H:    account_index = 0
    #  - 0:     change = receiving address
    #  - 0:     address_index increment to create a new payment address
    @staticmethod
    def create_extended_private_key(root_extended_private_key):
        command = ['cardano-address', 'key', 'child', '1852H/1815H/0H/0/0']
        output = run_command(command, input=root_extended_private_key, network=None)
        return output

    # Private Signing Key : Is used to sign / approve transactions for your wallet. As
    # you can imagine, it is very important to not expose this file to the public and
    # must be kept secure.
    #
    # The cborhex here contains of 4 parts:
    # 1. prefix 5880 - bytestring of 128 bytes
    # 2. signing key (64 bytes) - b0bf46232c7f0f58ad333030e43ffbea7c2bb6f8135bd05fb0d343ade8453c5eacc7ac09f77e16b635832522107eaa9f56db88c615f537aa6025e6c23da98ae8
    # 3. verification key (32 bytes) - fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834
    # 4. chain code (32 bytes) - b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a
    def create_extended_signing_key_file(self):
        command = ['cardano-cli', 'key', 'convert-cardano-address-key', '--shelley-payment-key', 
                   '--signing-key-file', self.extended_private_key_file,
                   '--out-file', self.signing_key_file]        
        output = run_command(command, None)
        return output

    # Public Verification Key : Is used to derive a Cardano wallet address, a wallet
    # address is basically the hash string value that you share to other users to provide
    # them a way to send ADA / tADA or other assets in the Cardano blockchain into your
    # wallet.
    #
    # The cborhex here contains of 3 parts:
    # 1. prefix 5840 - bytestring of 64 bytes
    # 2. verification key (32 bytes) - fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834
    # 3. chain code (32 bytes) - b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a    
    def create_extended_verification_key_file(self):
        command = ['cardano-cli', 'key', 'verification-key', '--signing-key-file', self.signing_key_file,
                   '--verification-key-file', self.verification_key_file]
        output = run_command(command, None)
        return output

    # following the example here: https://github.com/input-output-hk/cardano-addresses
    def generate_key_files(self, mnemonic):
        root_extended_private_key = Wallet.create_root_extended_private_key(mnemonic)
        write_to_file(self.root_extended_private_key_file, root_extended_private_key)

        extended_private_key = Wallet.create_extended_private_key(root_extended_private_key)
        write_to_file(self.extended_private_key_file, extended_private_key)

        self.create_extended_signing_key_file()
        self.create_extended_verification_key_file()

        print("Root extended private key = {}".format(root_extended_private_key))
        print("Extended private key = {}".format(extended_private_key))

    # Since we now have our payment key-pair (skey and vkey), the next step would be to generate a wallet
    # address.  Only the verification key (vkey) is used to generate the address.
    def create_address_file(self):
        command = ['cardano-cli', 'address', 'build', 
                   '--payment-verification-key-file', self.verification_key_file,
                   '--out-file', self.payment_address_file]
        output = run_command(command, cardano.get_network())
        return output

    def query_utxo(self):
        payment_address = self.get_payment_address()

        command = ['cardano-cli', 'query', 'utxo', '--address', payment_address]
        output = run_command(command, cardano.get_network())

        # Calculate total lovelace of the UTXO(s) inside the wallet address
        utxo_table = output.splitlines()
        total_lovelace = 0

        utxos = []
        for x in range(2, len(utxo_table)):
            cells = utxo_table[x].split()
            assets = []
            for x in range(4, len(cells), 3):
                if cells[x] == '+':
                    asset_amount = int(cells[x+1])
                    asset_name = cells[x+2]
                    asset = {'name': asset_name, 'amount': asset_amount}
                    assets.append(asset)

            utxos.append({'tx-hash':cells[0], 'tx-ix':int(cells[1]), 'amount': int(cells[2]), 'assets': assets})
            total_lovelace +=  int(cells[2])

        return (utxos, total_lovelace)

class Cardano:
    def __init__(self, network, protocol_parameters_file):
        self.network = network
        self.protocol_parameters_file = protocol_parameters_file
        self.protocol_parameters = {}

    def get_network(self):
        return self.network

    def query_tip(self):
        command = ['cardano-cli', 'query', 'tip']
        output = run_command(command, self.network)
        tip = json.loads(output)
        return tip

    def query_protocol_parameters(self):
        self.protocol_parameters = {}

        command = ['cardano-cli', 'query', 'protocol-parameters', '--out-file', self.protocol_parameters_file]
        output = run_command(command, self.network)

        with open(self.protocol_parameters_file, "r") as file:
            self.protocol_parameters = json.loads(file.read())
        return self.protocol_parameters

    def get_protocol_parameters_file(self):
        return self.protocol_parameters_file

    def get_protocol_parameters(self):
        return self.protocol_parameters

    def create_transfer_transaction_file(self, utxo_inputs, address_outputs, fee_amount, transaction_file):
        command = ['cardano-cli', 'transaction', 'build-raw']

        for utxo in utxo_inputs:
            command.append('--tx-in')
            command.append('{}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))

        for address in address_outputs:
            command.append('--tx-out')
            command.append('{}+{}{}'.format(address['address'], address['amount'], address['assets']))

        command.extend(['--fee', '{}'.format(fee_amount),
                        '--out-file', transaction_file])

        output = run_command(command, None)
        return output

    def create_mint_nft_transaction_file(self, utxo_inputs, address_output, fee_amount, 
                                         policy_name, nft_token_name, nft_token_amount, 
                                         transaction_file):
        policy_id = self.get_policy_id(policy_name)
        mint = '{} {}.{}'.format(nft_token_amount, policy_id, nft_token_name)
        
        invalid_hereafter = 0
        with open('policy/{}.script'.format(policy_name), "r") as file:
            script = json.loads(file.read())
            for s in script['scripts']:
                if s['type'] == 'before':
                    invalid_hereafter = s['slot']

        command = ['cardano-cli', 'transaction', 'build-raw', '--fee', '{}'.format(fee_amount)]

        assets = ''
        for utxo in utxo_inputs:
            command.append('--tx-in')
            command.append('{}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))
            for a in utxo['assets']:
                assets = assets + '+{} {}'.format(a['amount'], a['name'])

        command.extend(['--tx-out',
                        '{}+{}{}+{}'.format(address_output['address'], address_output['amount'], assets, mint)])

        command.extend(['--mint={}'.format(mint),
                        '--minting-script-file', 'policy/{}.script'.format(policy_name),
                        '--metadata-json-file', 'nft/{}_metadata.json'.format(nft_token_name),
                        '--invalid-hereafter', '{}'.format(invalid_hereafter),
                        '--out-file', transaction_file])

        output = run_command(command, None)
        return output

    def calculate_min_fee(self, transaction_file, tx_in_count, tx_out_count, witness_count):
        command = ['cardano-cli', 'transaction', 'calculate-min-fee', '--tx-body-file', transaction_file, 
                   '--tx-in-count', str(tx_in_count), '--tx-out-count', str(tx_out_count),
                   '--witness-count', str(witness_count),
                   '--protocol-params-file', self.protocol_parameters_file]
        output = run_command(command, self.network)
        cells = output.split()
        return int(cells[0])

    def sign_transaction(self, unsigned_transaction_file, signing_key_file, signed_transaction_file):
        command = ['cardano-cli', 'transaction', 'sign', '--tx-body-file', unsigned_transaction_file, 
                   '--signing-key-file', signing_key_file,
                   '--out-file', signed_transaction_file]
        output = run_command(command, self.network)
        return output

    def submit_transaction(self, transaction_file):
        command = ['cardano-cli', 'transaction', 'submit', '--tx-file', transaction_file]
        output = run_command(command, self.network)
        return output

    def create_new_policy_id(self, before_slot, wallet, policy_name):
        # create new keys for the policy
        command = ['cardano-cli', 'address', 'key-gen', 
                   '--verification-key-file', 'policy/{}.vkey'.format(policy_name), 
                   '--signing-key-file', 'policy/{}.skey'.format(policy_name)]
        run_command(command, None)

        # create signature hash from keys
        command = ['cardano-cli', 'address', 'key-hash', 
                   '--payment-verification-key-file', wallet.get_verification_key_file()]
        sig_key_hash = '185fb686016e956aaba95f4e9e38f33547cc02ec8947e177e9488a4b' #= run_command(command, None)

        # create script file requires sign by policy keys and only valid until specified slot
        with open('policy/{}.script'.format(policy_name), 'w') as file:
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
                   '--script-file', 'policy/{}.script'.format(policy_name)]
        output = run_command(command, None)
        with open('policy/{}_id'.format(policy_name), 'w') as file:
            file.write(output)

        return output

    def get_policy_id(self, policy_name):
        policy_id = None

        with open('policy/{}_id'.format(policy_name), 'r') as file:
            policy_id = file.read()

        return policy_id

class NftMint:
    def __init__(self):
        pass

    # https://pool.pm/test/metadata
    # https://www.youtube.com/watch?v=WP64LuFgdog
    def create_metadata(self, policy_id, token_name, description, nft_name, image):
        metadata_file = 'nft/{}_metadata.json'.format(token_name)
        with open(metadata_file, 'w') as file:
            file.write('{\r\n')
            file.write('    \"721\": {\r\n')
            file.write('        \"{}\": {}\r\n'.format(policy_id, '{'))
            file.write('            \"{}\": {}\r\n'.format(token_name, '{'))
            file.write('                \"name\": \"{}\",\r\n'.format(nft_name))
            file.write('                \"description\": \"{}\",\r\n'.format(description))
            file.write('                \"id\": {},\r\n'.format(1))
            file.write('                \"image\": \"{}\"\r\n'.format(image))
            file.write('            }\r\n')
            file.write('        }\r\n')
            file.write('    }\r\n')
            file.write('}\r\n')



def transfer_ada(cardano, from_wallet, to_wallet, lovelace_amount):
    # search utxo in from wallet containing the nft
    (from_utxos, from_total_lovelace) = from_wallet.query_utxo()
    assets = ''
    for utxo in from_utxos:
        for a in utxo['assets']:
            assets = assets + '+{} {}'.format(a['amount'], a['name'])

    print("From Total Lovelace: {}".format(from_total_lovelace))
    # Draft transaction for fee calculation
    outputs = [{'address': from_wallet.get_payment_address(), 'amount': 0, 'assets': assets},
               {'address': to_wallet.get_payment_address(), 'amount': 0, 'assets': ''}]
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transfer_ada_draft_tx')

    # Calculate fee & update values 
    fee = cardano.calculate_min_fee('transfer_ada_draft_tx', len(from_utxos), len(outputs), 1)
    print("Fee = {} lovelace".format(fee))
    outputs[0]['amount'] = from_total_lovelace - lovelace_amount - fee
    outputs[1]['amount'] = lovelace_amount

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transfer_ada_unsigned_tx')
   
    # Sign the transaction
    cardano.sign_transaction('transfer_ada_unsigned_tx', from_wallet.get_signing_key_file(), 'transfer_ada_signed_tx')

    #submit
    cardano.submit_transaction('transfer_ada_signed_tx')

def transfer_nft(cardano, nft_amount, nft_name, from_wallet, to_wallet):
    # search utxo in from wallet containing the nft
    (from_utxos, from_total_lovelace) = from_wallet.query_utxo()
    assets = ''
    for utxo in from_utxos:
        for a in utxo['assets']:
            if a['name'] == nft_name and a['amount'] >= nft_amount:
                a['amount'] -= nft_amount
            assets = assets + '+{} {}'.format(a['amount'], a['name'])

    print("From Total Lovelace: {}".format(from_total_lovelace))
    # Draft transaction for fee calculation
    outputs = [{'address': from_wallet.get_payment_address(), 'amount': 0, 'assets': assets},
               {'address': to_wallet.get_payment_address(), 'amount': 0, 'assets': '+{} {}'.format(nft_amount, nft_name)}]
    fee = 0
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transfer_nft_draft_tx')


    # https://github.com/input-output-hk/cardano-ledger-specs/blob/master/doc/explanations/min-utxo.rst
    # minUTxOValue is the minimum value if sending ADA only.  Since ADA plus a
    # custom NFT token is being sent the amount to send is larger.  500000 extra
    # seems to be ok.  Make it 1000000 to be sure.
    min_utxo_value = cardano.get_protocol_parameters()['minUTxOValue'] + 1000000

    # Calculate fee & update values 
    fee = cardano.calculate_min_fee('transfer_nft_draft_tx', len(from_utxos), len(outputs), 1)
    print("Fee = {} lovelace".format(fee))
    outputs[0]['amount'] = from_total_lovelace - min_utxo_value - fee
    outputs[1]['amount'] = min_utxo_value

    # Final unsigned transaction
    cardano.create_transfer_transaction_file(from_utxos, outputs, fee, 'transfer_nft_unsigned_tx')
   
    # Sign the transaction
    cardano.sign_transaction('transfer_nft_unsigned_tx', from_wallet.get_signing_key_file(), 'transfer_nft_signed_tx')

    #submit
    cardano.submit_transaction('transfer_nft_signed_tx')

def mint_nft(cardano, minting_wallet, policy_name, nft_token_name):
    (minting_utxos, minting_total_lovelace) = testnet1.query_utxo()

    # Mint an NFT funded by testnet1 wallet
    address_output = {'address': minting_wallet.get_payment_address(), 'amount': 0}
    fee = 0
    # draft
    cardano.create_mint_nft_transaction_file(minting_utxos, address_output, fee, policy_name, nft_token_name, 1, 'mint_nft_draft_tx')
    #fee
    fee = cardano.calculate_min_fee('mint_nft_draft_tx', len(minting_utxos), 1, 1)
    print("Fee = {} lovelace".format(fee))
    address_output['amount'] = minting_total_lovelace - fee
    #final
    cardano.create_mint_nft_transaction_file(minting_utxos, address_output, fee, policy_name, nft_token_name, 1, 'mint_nft_unsigned_tx')
    #sign
    cardano.sign_transaction('mint_nft_unsigned_tx', minting_wallet.get_signing_key_file(), 'mint_nft_signed_tx')
    #submit
    cardano.submit_transaction('mint_nft_signed_tx')

cardano = Cardano('testnet', 'testnet_protocol_parameters.json')
tip = cardano.query_tip()
tip_slot = tip['slot']
print("tip slot = {}".format(tip_slot))
cardano.query_protocol_parameters()

print("")
testnet1 = Wallet("testnet1", cardano)
print("testnet1 UTXOS:")
(tn1utxos, tn1_total_lovelace) = testnet1.query_utxo()
for utxo in tn1utxos:
    print("tx-hash = {}, tx-ix = {}, amount = {} lovelace".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
    for a in utxo['assets']:
        print('\t\t\t\t {} {}'.format(a['amount'], a['name']))

print("Total: {}".format(tn1_total_lovelace))
print("")

print("")
testnet2 = Wallet("testnet2", cardano)
print("testnet2 UTXOS:")
(tn2utxos, tn2_total_lovelace) = testnet2.query_utxo()
for utxo in tn2utxos:
    print("tx-hash = {}, tx-ix = {}, amount = {} lovelace".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
    for a in utxo['assets']:
        print('\t\t\t\t {} {}'.format(a['amount'], a['name']))

print("Total: {}".format(tn2_total_lovelace))
print("")

payment1 = Wallet("payment1", cardano)
print("payment1 UTXOS:")
(p1utxos, p1_total_lovelace) = payment1.query_utxo()
for utxo in p1utxos:
    print("tx-hash = {}, tx-ix = {}, amount = {}".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
    for a in utxo['assets']:
        print('\t\t {} {}'.format(a['amount'], a['name']))
print("Total: {}".format(p1_total_lovelace))
print("")

# Send ADA from testnet1 to payment1.  payment1 before: 1057000000
#transfer_ada(cardano, testnet1, payment1, 100000000)

# Send an NFT from testnet1 to payment1
#transfer_nft(cardano, 1, '2ac9560fe5d3afb760d9054d161786bbbf34e391ca44a7d091b4ad0b.TCRx001x001', 
#                     testnet1, payment1)


"""
# Lets mint an nft on testnet
policy_name = 'tcr_policy'
nft_token_name = 'TCRx001x001'
nft_name = "The Card Room 1.1 [1]"
# cardano.create_new_policy_id(tip_slot+100000, testnet1, policy_name)
policy_id = cardano.get_policy_id(policy_name)
nft = NftMint()
nft.create_metadata(policy_id, nft_token_name, "Another test creating an NFT", nft_name, "ipfs://QmRhTTbUrPYEw3mJGGhQqQST9k86v1DPBiTTWJGKDJsVFw")
mint_nft(cardano, testnet1, policy_name, nft_token_name)
"""
