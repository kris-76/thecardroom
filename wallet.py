
# https://github.com/input-output-hk/cardano-addresses

# Let's assume we have mnemonic
# $ cat recovery-phrase.prv
# nothing heart matrix fly sleep slogan tomato pulse what roof rail since plastic false enlist

# Construct root extended private key
# $ cardano-address key from-recovery-phrase Shelley < recovery-phrase.prv > root.xprv
# root_xsk1apjwjs3ksgm5mnnk0cc5v5emgv0hmafmmy8tffay5s2ffk69830whwznr46672ruucdzwwtv9upv72e4ylrypyz5m6cyh0p00t7n3u3agt20lv32j4kxcqlkzu78nzjx0ysxxlc2ghfz9prxfmrds802xsuhh404~

# Construct extended private key for account ix=0H, role=0 and address ix=0
# $ cardano-address key child 1852H/1815H/0H/0/0 < root.xprv > key.xsk
# addr_xsk1kzl5vgev0u843tfnxqcwg0lmaf7zhdhczddaqhas6dp6m6z98302e3avp8mhu94kxkpj2gss064f74km3rrptafh4fsztekz8k5c469shcvx35wrdmus3xemp984lcwhs0jdtl4pfcsrfspe00h9pej6rg8drvcv

# Create extended signing key using cardano-cli
# $ cardano-cli key convert-cardano-address-key --shelley-payment-key --signing-key-file key.xsk --out-file key.skey
# {
#     "type": "PaymentExtendedSigningKeyShelley_ed25519_bip32",
#     "description": "",
#     "cborHex": "5880b0bf46232c7f0f58ad333030e43ffbea7c2bb6f8135bd05fb0d343ade8453c5eacc7ac09f77e16b635832522107eaa9f56db88c615f537aa6025e6c23da98ae8fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a"
# }

# The cborhex here contains of 4 parts:
# 1. prefix 5880 - bytestring of 128 bytes
# 2. signing key (64 bytes) - b0bf46232c7f0f58ad333030e43ffbea7c2bb6f8135bd05fb0d343ade8453c5eacc7ac09f77e16b635832522107eaa9f56db88c615f537aa6025e6c23da98ae8
# 3. verification key (32 bytes) - fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834
# 4. chain code (32 bytes) - b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a

# Create corresponding verification key using cardano-cli
# $ cardano-cli key verification-key --signing-key-file key.skey --verification-key-file key.vkey
# {
#     "type": "PaymentExtendedVerificationKeyShelley_ed25519_bip32",
#     "description": "",
#     "cborHex": "5840fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a"
# }
# The cborhex here contains of 3 parts:
# 1. prefix 5840 - bytestring of 64 bytes
# 2. verification key (32 bytes) - fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834
# 3. chain code (32 bytes) - b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a

# Rule for prefixes:
#   - CBOR-encoded bytestring (which is what the 58 identifies)
#   - size (80 means 128 bytes, whereas 40 means 64 bytes, 20 means 32 bytes)

# Create verification key hash using cardano-cli
# $ cardano-cli address key-hash --payment-verification-key-file key.vkey > key.hash
# 0185545935760c5e370d01e6f4fedbb89b7fd79e115f2837cfab9ea8

# Alternatively, we can create non-extended key
# $ cardano-address key public --without-chain-code < key.xsk > key.vk
# addr_vk1lwalvsgwy3fj7d0fy707hvy96txqtvaj4ksa7al2r9g7k6208q6qmrv9k3

# Also, take notice that signing key can be translated to cborhex:
# $ cat key.xsk | bech32
# b0bf46232c7f0f58ad333030e43ffbea7c2bb6f8135bd05fb0d343ade8453c5eacc7ac09f77e16b635832522107eaa9f56db88c615f537aa6025e6c23da98ae8b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a
# (signing key and chain code appended)

# Moreover, basing on key.vk one can get hash
# $ cardano-cli address key-hash --payment-verification-key $(cat key.vk) > key1.hash
# 0185545935760c5e370d01e6f4fedbb89b7fd79e115f2837cfab9ea8

# Within cardano-addresses one can get cborhex of verification key (with chain code)
# $ cardano-address key public --with-chain-code < key.xsk | bech32
# fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834b0be1868d1c36ef9089b3b094f5fe1d783e4d5fea14e2034c0397bee50e65a1a
# (verification key and chain code appended)

# Within cardano-addresses one can get cborhex of verification key (without chain code)
# $ cardano-address key public --without-chain-code < key.xsk | bech32
# fbbbf6410e24532f35e9279febb085d2cc05b3b2ada1df77ea1951eb694f3834
# (verification key without chain code)

# Then, we can get compute hash (but here we need to use without chain code):
# $ cardano-address key public --without-chain-code < key.xsk | cardano-address key hash | bech32
# 0185545935760c5e370d01e6f4fedbb89b7fd79e115f2837cfab9ea8


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
        print('{} '.format(c), end='')
    print('')

def run_command(command, network, input=None):
    envvars = os.environ

    if network != None:
        envvars[node_socket_env['active']] = os.environ[node_socket_env[network]]
        command.extend(networks[network])

    print_command(command)
    completed = subprocess.run(command, check=True, capture_output=True, text=True, input=input, env=envvars)

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

    # Create a mnemonic phrase that can be used with cardano-wallet, yoroi, dadaelus, etc....
    @staticmethod
    def create_mnemonic_phrase():
        completed = subprocess.run(['cardano-wallet', 'recovery-phrase', 'generate'], 
                                   check=True, capture_output=True, text=True)
        output = completed.stdout.strip('\r\n')
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
            utxos.append({'tx-hash':cells[0], 'tx-ix':int(cells[1]), 'amount': int(cells[2])})
            total_lovelace +=  int(cells[2])

        return (utxos, total_lovelace)

class Cardano:
    def __init__(self, network):
        self.network = network
        self.protocol_parameters = {}

    def get_network(self):
        return self.network

    def query_tip(self):
        command = ['cardano-cli', 'query', 'tip']
        output = run_command(command, self.network)
        tip = json.loads(output)
        return tip

    def query_protocol_parameters(self, protocol_parameters_file):
        self.protocol_parameters = {}

        command = ['cardano-cli', 'query', 'protocol-parameters', '--out-file', protocol_parameters_file]
        output = run_command(command, self.network)

        with open(protocol_parameters_file, "r") as file:
            self.protocol_parameters = json.loads(file.read())
        return self.protocol_parameters

    def create_transaction_file_2out(self, utxo, utxo_number, wallet_from, from_amount, wallet_to, to_amount, fee_amount, transaction_file):
        command = ['cardano-cli', 'transaction', 'build-raw', 
                   '--tx-in', '{}#{}'.format(utxo, utxo_number), 
                   '--tx-out', '{}+{}'.format(wallet_from.get_payment_address(), from_amount), 
                   '--tx-out', '{}+{}'.format(wallet_to.get_payment_address(), to_amount), 
                   '--fee', '{}'.format(fee_amount),
                   '--out-file', transaction_file]
        output = run_command(command, None)
        return output

    def create_transaction_file_1out(self, utxo, utxo_number, wallet_to, to_amount, fee_amount, transaction_file):
        command = ['cardano-cli', 'transaction', 'build-raw', 
                   '--tx-in', '{}#{}'.format(utxo, utxo_number), 
                   '--tx-out', '{}+{}'.format(wallet_to.get_payment_address(), to_amount), 
                   '--fee', '{}'.format(fee_amount),
                   '--out-file', transaction_file]
        output = run_command(command, None)
        return output

    def create_transaction_file(self, utxo_inputs, address_outputs, fee_amount, transaction_file):
        command = ['cardano-cli', 'transaction', 'build-raw']

        for utxo in utxo_inputs:
            command.append('--tx-in')
            command.append('{}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))

        for address in address_outputs:
            command.append('--tx-out')
            command.append('{}+{}'.format(address['address'], address['amount']))

        command.extend(['--fee', '{}'.format(fee_amount),
                        '--out-file', transaction_file])

        output = run_command(command, None)
        return output

    def calculate_min_fee(self, transaction_file, tx_in_count, tx_out_count, witness_count, protocol_parameters_file):
        command = ['cardano-cli', 'transaction', 'calculate-min-fee', '--tx-body-file', transaction_file, 
                   '--tx-in-count', str(tx_in_count), '--tx-out-count', str(tx_out_count),
                   '--witness-count', str(witness_count),
                   '--protocol-params-file', protocol_parameters_file]
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

    def create_new_policy_id(self, before_slot, name):
        # create new keys for the policy
        command = ['cardano-cli', 'address', 'key-gen', 
                   '--verification-key-file', 'policy/{}.vkey'.format(name), 
                   '--signing-key-file', 'policy/{}.skey'.format(name)]
        run_command(command, None)

        # create signature hash from keys
        command = ['cardano-cli', 'address', 'key-hash', 
                   '--payment-verification-key-file', 'policy/{}.vkey'.format(name)]
        sig_key_hash = run_command(command, None)

        # create script file requires sign by policy keys and only valid until specified slot
        with open('policy/{}.script'.format(name), 'w') as file:
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
                   '--script-file', 'policy/{}.script'.format(name)]
        output = run_command(command, None)
        with open('policy/{}_id'.format(name), 'w') as file:
            file.write(output)
        return output

    

cardano = Cardano('testnet')
tip = cardano.query_tip()
tip_slot = tip['slot']
print("tip slot = {}".format(tip_slot))

cardano.query_protocol_parameters('protocol_parameters.json')

# Lets mint an nft on testnet
testnet1 = Wallet("testnet1", cardano)

print("testnet1 UTXOS:")
(p2utxos, total_lovelace) = testnet1.query_utxo()
for utxo in p2utxos:
    print("tx-hash = {}, tx-ix = {}, amount = {}".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
print("Total: {}".format(total_lovelace))

# don't want to create a new policy keys &id every time so comment this out
# cardano.create_new_policy_id(tip_slot+10000, 'tcr_policy')


"""
payment1 = Wallet("payment1", cardano)
testnet1 = Wallet("testnet1", cardano)

print("")
print("payment1 UTXOS:")
(p1utxos, total_lovelace) = payment1.query_utxo()
for utxo in p1utxos:
    print("tx-hash = {}, tx-ix = {}, amount = {}".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
print("Total: {}".format(total_lovelace))
print("")
p1_total = total_lovelace

print("testnet1 UTXOS:")
(p2utxos, total_lovelace) = testnet1.query_utxo()
for utxo in p2utxos:
    print("tx-hash = {}, tx-ix = {}, amount = {}".format(utxo['tx-hash'], utxo['tx-ix'], utxo['amount'], ))
print("Total: {}".format(total_lovelace))

"""

# an output must be greater than some minimum amount.  
""" # draft transaction used to calculate fee
cardano.create_transaction_file_2out(p2utxos[0]['tx-hash'], p2utxos[0]['tx-ix'], payment2, 0, payment1, 0, 0, 'p2_to_p1_draft_tx')

# calculate fee
fee = cardano.calculate_min_fee('p2_to_p1_draft_tx', 1, 2, 1, 'protocol_parameters.json')
print("Fee = {} lovelace".format(fee))

#create final transaction to send 150000000 lovelace from wallet2 to wallet 1
p1_amount = p2utxos[0]['amount'] - 10000000 - fee
p2_amount = 10000000
cardano.create_transaction_file_2out(p2utxos[0]['tx-hash'], p2utxos[0]['tx-ix'], 
                               payment2, p2_amount, payment1, p1_amount, 
                               fee, 'p2_to_p1_tx_unsigned')

# sign transaction
cardano.sign_transaction('p2_to_p1_tx_unsigned', payment2.get_signing_key_file(), 'p2_to_p1_tx_signed')

# submit transaction
cardano.submit_transaction('p2_to_p1_tx_signed')
 """

# To send all ADA from a wallet, its output can not be 0.  Just remove it.
"""
# send remaining 10000000 lovelace from payment2 to payment1
cardano.create_transaction_file_1out(p2utxos[0]['tx-hash'], p2utxos[0]['tx-ix'], payment1, 0, 0, 'p2_to_p1_draft_tx')
fee = cardano.calculate_min_fee('p2_to_p1_draft_tx', 1, 1, 1, 'protocol_parameters.json')
print("Fee = {} lovelace".format(fee))
p1_amount = p2utxos[0]['amount'] - fee
cardano.create_transaction_file_1out(p2utxos[0]['tx-hash'], p2utxos[0]['tx-ix'], 
                               payment1, p1_amount, fee, 'p2_to_p1_tx_unsigned')
cardano.sign_transaction('p2_to_p1_tx_unsigned', payment2.get_signing_key_file(), 'p2_to_p1_tx_signed')
cardano.submit_transaction('p2_to_p1_tx_signed')
"""

"""
# send all from payment1 to testnet1
outputs = [{'address': testnet1.get_payment_address(), 'amount': 0}]

cardano.create_transaction_file(p1utxos, outputs, 0, 'p1_to_t1_draft_tx')
fee = cardano.calculate_min_fee('p1_to_t1_draft_tx', 3, 1, 1, 'protocol_parameters.json')
print("Fee = {} lovelace".format(fee))

outputs[0]['amount'] = p1_total - fee
cardano.create_transaction_file(p1utxos, outputs, fee, 'p1_to_t1_tx_unsigned')

cardano.sign_transaction('p1_to_t1_tx_unsigned', payment1.get_signing_key_file(), 'p1_to_t1_tx_signed')
cardano.submit_transaction('p1_to_t1_tx_signed')
"""



