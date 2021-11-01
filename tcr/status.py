#
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

from tcr.wallet import Wallet
from tcr.wallet import WalletExternal
from tcr.cardano import Cardano
from tcr.database import Database
import logging
import argparse
import tcr.command
import tcr.nftmint
import traceback

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network', required=True,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='Which network to use, [mainnet | testnet]')
    parser.add_argument('--wallet',  required=False,
                                    action='store',
                                    type=str,
                                    default=None,
                                    metavar='NAME',
                                    help='Dump UTXOs from wallet')
    parser.add_argument('--policy',  required=False,
                                    action='store',
                                    type=str,
                                    default=None,
                                    metavar='NAME',
                                    help='')
    args = parser.parse_args()
    network = args.network
    wallet_name = args.wallet
    policy_name = args.policy

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'status')
    logger = logging.getLogger(network)

    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']

    database = Database('{}.ini'.format(network))
    database.open()
    meta = database.query_chain_metadata()
    db_size = database.query_database_size()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.info('Database Chain Metadata: {} / {}'.format(meta[1], meta[2]))
    logger.info('Database Size: {}'.format(db_size))
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('Sync Progress: {}'.format(sync_progress))

    wallet = None
    if wallet_name != None:
        if wallet_name.startswith('addr'):
            wallet = WalletExternal('external', cardano.get_network, wallet_name)
        else:
            wallet = Wallet(wallet_name, cardano.get_network())

        if not wallet.exists():
            logger.error('Wallet: <{}> does not exist'.format(wallet_name))
            raise Exception('Wallet: <{}> does not exist'.format(wallet_name))

        stake_address = database.query_stake_address(wallet.get_payment_address(Wallet.ADDRESS_INDEX_MINT))
        logger.info('   Root address = {}'.format(wallet.get_payment_address(Wallet.ADDRESS_INDEX_ROOT)))
        logger.info('   Mint address = {}'.format(wallet.get_payment_address(Wallet.ADDRESS_INDEX_MINT)))
        logger.info('Presale address = {}'.format(wallet.get_payment_address(Wallet.ADDRESS_INDEX_PRESALE)))
        logger.info('  Stake address = {}'.format(stake_address))

        cardano.dump_utxos_sorted(database, wallet)

    if policy_name != None:
        policies = policy_name.split(',')
        logger.info('')

        #logger.info("By Token: ")
        by_address = {}
        i = 1
        for policy in policies:
            if cardano.get_policy_id(policy) == None:
                logger.error('Policy: <{}> does not exist'.format(policy))
                raise Exception('Policy: <{}> does not exist'.format(policy))

            tokens = database.query_current_owner(cardano.get_policy_id(policy))
            logger.info('{} = {} tokens'.format(policy, len(tokens)))

            keys = list(tokens.keys())
            keys.sort()
            for name in keys:
                address = tokens[name]['address']
                slot = tokens[name]['slot']
                logger.info('{}.  {} owned by {} at slot {}'.format(i, name, address, slot))
                i += 1

                if address in by_address:
                    by_address[address].append(name)
                else:
                    by_address[address] = [name]

        holders = list(by_address.items())
        def sort_by_length(item):
            return len(item[1])
        holders.sort(key=sort_by_length)
        logger.info('')
        logger.info('')
        logger.info('By Owner:')
        logger.info('len = {}'.format(len(holders)))
        i = 1
        for holder in holders:
            logger.info('{: 4}.  {}({})'.format(i, holder[0], len(holder[1])))
            tokens = holder[1]

            token_str = ''
            j = 0
            for token in tokens:
                if len(token_str) == 0:
                    token_str += token
                else:
                    token_str += ', ' + token
                j += 1
                if j == 8:
                    logger.info('       {}'.format(token_str))
                    j = 0
                    token_str = ''

            if j > 0:
                logger.info('       {}'.format(token_str))
            i += 1


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
