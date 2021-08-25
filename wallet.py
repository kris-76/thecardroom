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
# https://docs.cardano.org/introduction

import json
import os
from command import Command

class Wallet:
    def __init__(self, name, cardano):
        self.name = name
        self.cardano = cardano
        self.mnemonic_phrase_file = 'wallet/{}/{}.mnemonic'.format(cardano.get_network(), name)
        self.root_extended_private_key_file = 'wallet/{}/{}_root.xprv'.format(cardano.get_network(), name)
        self.extended_private_key_file = 'wallet/{}/{}_key.xsk'.format(cardano.get_network(), name)
        self.signing_key_file = 'wallet/{}/{}_key.skey'.format(cardano.get_network(), name)
        self.verification_key_file = 'wallet/{}/{}_key.vkey'.format(cardano.get_network(), name)
        self.payment_address = None
        self.payment_address_file = 'wallet/{}/{}_payment.addr'.format(cardano.get_network(), name)

    def get_name(self):
        return self.name

    def exists(self):
        return os.path.exists(self.signing_key_file) and os.path.exists(self.verification_key_file) and os.path.exists(self.payment_address_file)

    def create_new_wallet(self):
        mnemonic = Wallet.create_mnemonic_phrase()
        Command.write_to_file(self.mnemonic_phrase_file, mnemonic)
        self.generate_key_files(mnemonic)
        self.create_address_file()
        return self.exists()

    def get_payment_address(self):
        self.payment_address = None

        with open(self.payment_address_file, 'r') as file:
            self.payment_address = file.read()

        return self.payment_address

    def get_signing_key_file(self):
        return self.signing_key_file

    def get_verification_key_file(self):
        return self.verification_key_file

    # Create a mnemonic phrase that can be used with cardano-wallet, yoroi, dadaelus, etc....
    @staticmethod
    def create_mnemonic_phrase():
        command = ['cardano-wallet', 'recovery-phrase', 'generate']
        output = Command.run(command, network=None)
        return output

    @staticmethod
    def create_root_extended_private_key(mnemonic):
        command = ['cardano-address', 'key', 'from-recovery-phrase', 'Shelley']
        output = Command.run(command, input=mnemonic, network=None)
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
        output = Command.run(command, input=root_extended_private_key, network=None)
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
        output = Command.run(command, None)
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
        output = Command.run(command, None)
        return output

    # following the example here: https://github.com/input-output-hk/cardano-addresses
    def generate_key_files(self, mnemonic):
        root_extended_private_key = Wallet.create_root_extended_private_key(mnemonic)
        Command.write_to_file(self.root_extended_private_key_file, root_extended_private_key)

        extended_private_key = Wallet.create_extended_private_key(root_extended_private_key)
        Command.write_to_file(self.extended_private_key_file, extended_private_key)

        self.create_extended_signing_key_file()
        self.create_extended_verification_key_file()

    # Since we now have our payment key-pair (skey and vkey), the next step would be to generate a wallet
    # address.  Only the verification key (vkey) is used to generate the address.
    def create_address_file(self):
        command = ['cardano-cli', 'address', 'build', 
                   '--payment-verification-key-file', self.verification_key_file,
                   '--out-file', self.payment_address_file]
        output = Command.run(command, self.cardano.get_network())
        return output

    def query_utxo(self):
        payment_address = self.get_payment_address()

        command = ['cardano-cli', 'query', 'utxo', '--address', payment_address]
        output = Command.run(command, self.cardano.get_network())

        # Calculate total lovelace of the UTXO(s) inside the wallet address
        utxo_table = output.splitlines()
        total_lovelace = 0

        utxos = []
        for x in range(2, len(utxo_table)):
            cells = utxo_table[x].split()
            assets = {}
            for x in range(4, len(cells), 3):
                if cells[x] == '+':
                    asset_amount = int(cells[x+1])
                    asset_name = cells[x+2]
                    assets[asset_name] = asset_amount
 
            utxos.append({'tx-hash':cells[0], 'tx-ix':int(cells[1]), 'amount': int(cells[2]), 'assets': assets})
            total_lovelace +=  int(cells[2])

        return (utxos, total_lovelace)

class WalletExternal(Wallet):
    def __init__(self, name, payment_address, cardano):
        self.name = name
        self.cardano = cardano
        self.payment_address = payment_address

        self.mnemonic_phrase_file = None
        self.root_extended_private_key_file = None
        self.extended_private_key_file = None
        self.signing_key_file = None
        self.verification_key_file = None
        self.payment_address_file = None

    def exists(self):
        return len(self.payment_address) > 0

    def get_verification_key_file(self):
        raise Exception("External wallet does not have verification key file")

    def get_payment_address(self):
        return self.payment_address

