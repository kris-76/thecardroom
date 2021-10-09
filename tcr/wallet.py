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
Author: Kris Henderson
"""

from typing import Tuple
import os
import logging

from tcr.command import Command

logger = logging.getLogger('wallet')

class Wallet:
    """
    The Wallet class is used to create a new wallet and all operations
    associated with creating wallets.

    Commands based on https://github.com/input-output-hk/cardano-addresses
    """

    ADDRESS_INDEX_ROOT = 0
    ADDRESS_INDEX_MINT = 1
    ADDRESS_INDEX_PRESALE = 2

    def __init__(self,
                 name: str,
                 network: str):
        """
        Construct a new instance of Wallet.

        @param name An arbitrary name for the wallet.  Mainly used to store wallet
                    data / keys in various files.
        @param network The network this wallet exists on.  Valid values are 'testnet'
                       and 'mainnet'.  This parameter should use Cardano.get_network().
                       This value is also used by some methods that run a cardano-cli
                       command to pass correct parameters into it.
        """

        self.name = name
        self.network = network
        self.payment_address = None
        self.delegated_payment_address = None
        self.stake_address = None
        self.save_extra_files = False

        self.mnemonic_phrase_file = 'wallet/{}/{}.mnemonic'.format(self.network, name)
        self.root_private_key_file = 'wallet/{}/{}_root.xprv'.format(self.network, name)
        self.payment_private_key_file_base = 'wallet/{}/{}_{}_key.xsk'.format(self.network, name, '{}')
        self.stake_private_key_file = 'wallet/{}/{}_stake_key.xsk'.format(self.network, name)
        self.payment_address_file_base = 'wallet/{}/{}_{}_payment.addr'.format(self.network, name, '{}')
        self.delegated_payment_address_file_base = 'wallet/{}/{}_{}_delegated_payment.addr'.format(self.network, name, '{}')
        self.stake_address_file = 'wallet/{}/{}_stake.addr'.format(self.network, name)
        self.signing_key_file_base = 'wallet/{}/{}_{}_key.skey'.format(self.network, name, '{}')
        self.verification_key_file_base = 'wallet/{}/{}_{}_key.vkey'.format(self.network, name, '{}')

    def get_name(self) -> str:
        """
        Return the name of the wallet.
        """

        return self.name

    def exists(self) -> bool:
        """
        Check to make sure the default files exist.
        """

        if not os.path.isfile(self.signing_key_file_base.format(0)):
            return False

        if not os.path.isfile(self.verification_key_file_base.format(0)):
            return False

        if not os.path.isfile(self.payment_address_file_base.format(0)):
            return False

        if not os.path.isfile(self.signing_key_file_base.format(1)):
            return False

        if not os.path.isfile(self.verification_key_file_base.format(1)):
            return False

        if not os.path.isfile(self.payment_address_file_base.format(1)):
            return False

        return True

    def setup_wallet(self,
                     mnemonic: str=None,
                     save_extra_files: bool=False) -> bool:
        """"
        Create a new wallet or recover a wallet if the mnemonic is given.

        @param mnemonic Recover a wallet from this mnemonic phrase.  If not specified
                        then a new phrase and wallet will be generated.
        @param save_extra_files Store extra files not normally needed.

        This will setup two addresses on the wallet.  A 'private' wallet at
        index 0 and a 'public' wallet at index 1.

        @return True if the wallet was successfully created.
        """

        # First create wallet for address index 0
        idx = 0

        logger.debug('Create new wallet: \'{}\''.format(self.name))
        if self.exists():
            logger.warning('Create new wallet: \'{}\' already exists'.format(self.name))
            raise Exception("Wallet already exists.")

        self.save_extra_files = save_extra_files

        if mnemonic == None:
            logger.debug('Generate new mnemonic')
            mnemonic = Wallet.generate_mnemonic_phrase()
        else:
            logger.debug('Recover mnemonic')
        Command.write_to_file(self.mnemonic_phrase_file, mnemonic)

        root_private_key = Wallet.generate_root_private_key(mnemonic)
        Command.write_to_file(self.root_private_key_file, root_private_key)

        (payment_private_key, payment_verification_key) = Wallet.generate_payment_verification_key(root_private_key, idx)
        fname = self.payment_private_key_file_base.format(idx)
        Command.write_to_file(fname, payment_private_key)

        (stake_private_key, stake_verification_key) = Wallet.generate_stake_verification_key(root_private_key)
        if self.save_extra_files:
            Command.write_to_file(self.stake_private_key_file, stake_private_key)

        payment_address = Wallet.generate_payment_address(self.network, payment_verification_key)
        self.payment_address = payment_address
        fname = self.payment_address_file_base.format(idx)
        Command.write_to_file(fname, payment_address)

        delegated_payment_address = Wallet.generate_delegated_payment_address(stake_verification_key, payment_address)
        self.delegated_payment_address = delegated_payment_address
        fname = self.delegated_payment_address_file_base.format(idx)
        Command.write_to_file(fname, delegated_payment_address)

        # Stake address not used.  Maybe later?
        #stake_address = Wallet.generate_stake_address(self.network, stake_verification_key)
        #Command.write_to_file(self.stake_address_file, stake_address)

        self.create_signing_key_file(idx)
        self.create_verification_key_file(idx)

        # Then create address index 1
        idx = 1
        self.setup_address(idx)
        return self.exists()

    def setup_address(self,
                      idx: int) -> None:
        """
        Create new addresses for the specied index.

        @param idx Index for the address
        """

        with open(self.root_private_key_file, 'r') as file:
            root_private_key = file.read()

            (payment_private_key, payment_verification_key) = Wallet.generate_payment_verification_key(root_private_key, idx)
            fname = self.payment_private_key_file_base.format(idx)
            Command.write_to_file(fname, payment_private_key)

            payment_address = Wallet.generate_payment_address(self.network, payment_verification_key)
            self.payment_address = payment_address
            fname = self.payment_address_file_base.format(idx)
            Command.write_to_file(fname, payment_address)

            (stake_private_key, stake_verification_key) = Wallet.generate_stake_verification_key(root_private_key)

            delegated_payment_address = Wallet.generate_delegated_payment_address(stake_verification_key, payment_address)
            self.delegated_payment_address = delegated_payment_address
            fname = self.delegated_payment_address_file_base.format(idx)
            Command.write_to_file(fname, delegated_payment_address)

            self.create_signing_key_file(idx)
            self.create_verification_key_file(idx)

    def get_payment_address(self,
                            idx: int=1,
                            delegated: bool=True) -> str:
        """
        Get the payment address for the specified index, delegated or not.

        @param idx Index for the address to get.
        @param delegated Default = True.  True = return a delegated address.
        """

        if delegated and os.path.isfile(self.delegated_payment_address_file_base.format(idx)):
            return self.get_delegated_payment_address(idx)

        self.payment_address = None
        addr_file = self.payment_address_file_base.format(idx)

        try:
            with open(addr_file, 'r') as file:
                self.payment_address = file.read()
        except FileNotFoundError as e:
            self.payment_address = None

        return self.payment_address

    def get_delegated_payment_address(self,
                                      idx: int=1) -> str:
        """
        Get the delegated payment address for the specified index.

        @param idx Index for the address to get.
        @param delegated Default = True.  True = return a delegated address.
        """

        self.delegated_payment_address = None
        addr_file = self.delegated_payment_address_file_base.format(idx)
        with open(addr_file, 'r') as file:
            self.delegated_payment_address = file.read()

        return self.delegated_payment_address

    def get_signing_key_file(self,
                             idx: int) -> str:
        """
        Get the signing key file for the given index.
        """

        return self.signing_key_file_base.format(idx)

    def get_verification_key_file(self, idx: int) -> str:
        """
        Get the verification key file for the given index.
        """

        return self.verification_key_file_base.format(idx)

    # Create a mnemonic phrase that can be used with cardano-wallet, yoroi, dadaelus, etc....
    @staticmethod
    def generate_mnemonic_phrase():
        command = ['cardano-address', 'recovery-phrase', 'generate']
        output = Command.run(command, network=None)
        logger.debug('Generate Mnemonic Phrase: {}'.format(output))
        return output

    @staticmethod
    def generate_root_private_key(mnemonic: str) -> str:
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
    def generate_payment_verification_key(root_private_key: str, idx: int = 0) -> Tuple[str, str]:
        command = ['cardano-address', 'key', 'child', '1852H/1815H/0H/0/{}'.format(idx)]
        payment_private_key = Command.run(command, input=root_private_key, network=None)

        command = ['cardano-address', 'key', 'public', '--with-chain-code']
        payment_verification_key = Command.run(command, input=payment_private_key, network=None)
        return (payment_private_key, payment_verification_key)

    @staticmethod
    def generate_stake_verification_key(root_private_key: str) -> Tuple[str, str]:
        command = ['cardano-address', 'key', 'child', '1852H/1815H/0H/2/0']
        stake_private_key = Command.run(command, input=root_private_key, network=None)

        command = ['cardano-address', 'key', 'public', '--with-chain-code']
        stake_verification_key = Command.run(command, input=stake_private_key, network=None)
        return (stake_private_key, stake_verification_key)

    @staticmethod
    def generate_payment_address(network: str, payment_verification_key: str) -> str:
        command = ['cardano-address', 'address', 'payment', '--network-tag', network]
        output = Command.run(command, input=payment_verification_key, network=None)
        return output

    @staticmethod
    def generate_delegated_payment_address(stake_verification_key: str, payment_address: str) -> str:
        command = ['cardano-address', 'address', 'delegation', stake_verification_key]
        output = Command.run(command, input=payment_address, network=None)
        return output

    @staticmethod
    def generate_stake_address(network: str, stake_verification_key: str) -> str:
        command = ['cardano-address', 'address', 'stake', '--network-tag', network]
        output = Command.run(command, input=stake_verification_key, network=None)
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
    def create_signing_key_file(self, idx: int):
        command = ['cardano-cli', 'key', 'convert-cardano-address-key', '--shelley-payment-key',
                   '--signing-key-file', self.payment_private_key_file_base.format(idx),
                   '--out-file', self.signing_key_file_base.format(idx)]
        output = Command.run(command, None)
        logger.debug("Create Signing Key File: {}".format(self.signing_key_file_base.format(idx)))
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
    def create_verification_key_file(self, idx: int):
        command = ['cardano-cli', 'key', 'verification-key', '--signing-key-file', self.signing_key_file_base.format(idx),
                   '--verification-key-file', self.verification_key_file_base.format(idx)]
        output = Command.run(command, None)
        logger.debug('Create Verification Key File: {}'.format(self.verification_key_file_base.format(idx)))
        return output

class WalletExternal(Wallet):
    """
    Create an instance of Wallet where only a public payment address is known.
    This is used when transfering lovelace or other assets from our wallet to
    another users wallet.
    """

    def __init__(self, name: str, network: str, payment_address: str):
        """
        Create an instance of WalletExternal.

        @param name @see Wallet.__init__
        @param network @see Wallet.__init__
        @param payment_address The public payment address to receive assets
        """

        self.name = name
        self.network = network
        self.payment_address = payment_address
        self.delegated_payment_address = None
        self.stake_address = None
        self.save_extra_files = False

        self.mnemonic_phrase_file = None
        self.root_private_key_file = None
        self.payment_private_key_file = None
        self.stake_private_key_file = None
        self.payment_address_file = None
        self.delegated_payment_address_file = None
        self.stake_address_file = None
        self.signing_key_file = None
        self.verification_key_file = None

    def exists(self):
        return len(self.payment_address) > 0

    def get_verification_key_file(self):
        raise Exception("External wallet does not have verification key file")

    def get_payment_address(self, idx: int = 1, delegated: bool=True):
        return self.payment_address

    def get_delegated_payment_address(self, idx: int = 1, delegated: bool=True):
        return self.payment_address
