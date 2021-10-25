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
from tcr.cardano import Cardano
from tcr.database import Database
import logging
import argparse
import traceback
import tcr.command
import tcr.nftmint
import json

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network', required=True,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='Network for the wallet, [mainnet | testnet]')
    parser.add_argument('--drop',  required=True,
                                    action='store',
                                    type=str,
                                    default=None,
                                    metavar='NAME',
                                    help='drop name (for prices)')
    parser.add_argument('--output', required=True,
                                    action='store',
                                    type=str,
                                    default=None,
                                    metavar='NAME',
                                    help='filename for whitelist results')

    args = parser.parse_args()
    network = args.network
    drop_name = args.drop
    address_index = Wallet.ADDRESS_INDEX_PRESALE
    output = args.output

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'genwhitelist')
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

    metametadata = tcr.nftmint.get_metametadata(cardano, drop_name)
    policy_name = metametadata['policy']
    wallet_name = cardano.get_policy_owner(policy_name)

    if wallet_name == None:
        logger.error('Policy owner not defined for policy: {}'.format(policy_name))
        raise Exception('Policy owner not defined for policy: {}'.format(policy_name))

    wallet = Wallet(wallet_name, cardano.get_network())
    if not wallet.exists():
        logger.error('Wallet: <{}> does not exist'.format(wallet_name))
        raise Exception('Wallet: <{}> does not exist'.format(wallet_name))

    if wallet.get_payment_address(address_index) == None:
        logger.warning("Address Index {} does not exist for wallet {}".format(address_index,
                                                                              wallet.get_name()))
        wallet.setup_address(address_index)
        logger.warning("Wallet <{}>: Create new address: {}".format(wallet.get_name(),
                                                                    wallet.get_payment_address(address_index)))

    logger.info("Wallet <{}>: Process whitelist on: {}".format(wallet.get_name(),
                                                               wallet.get_payment_address(address_index)))
    stake_address = database.query_stake_address(wallet.get_payment_address(address_index))
    logger.info('      address = {}'.format(wallet.get_payment_address(address_index)))
    logger.info('Stake address = {}'.format(stake_address))

    by_address = {}
    # TODO: Generalize for any policy / token
    if cardano.get_policy_id('tcr_series_1') != None:
        tokens = database.query_current_owner(cardano.get_policy_id('tcr_series_1'))
        for name in tokens:
            address = tokens[name]['address']
            slot = tokens[name]['slot']

            if address in by_address:
                by_address[address].append(name)
            else:
                by_address[address] = [name]
    else:
        logger.error('WARNING - WARNING - WARNING')
        logger.error('Policy: <{}> does not exist'.format('tcr_series_1'))
        logger.error('WARNING - WARNING - WARNING')

    hodlers = list(by_address.items())
    def sort_by_length(item):
        return len(item[1])
    hodlers.sort(key=sort_by_length)

    logger.info('HODLERS = {}'.format(len(hodlers)))
    for hodler in hodlers:
        hodler[1].sort()

    (utxos, lovelace) = cardano.query_utxos(wallet, [wallet.get_payment_address(address_index)])
    utxos = cardano.query_utxos_time(database, utxos)
    utxos.sort(key=lambda item : item['slot-no'])

    for price in metametadata['presale']:
        logger.info('{} lovelace = {} NFTs'.format(price, metametadata['presale'][price]))

    print('')
    presale = {"whitelist": []}
    used_special = False
    total_purchased = 0
    total_bonus = 0
    for utxo in utxos:
        nfts_total = 0
        nfts_purchased = 0
        nfts_bonus = 0

        if str(utxo['amount']) in metametadata['presale']:
            nfts_purchased = metametadata['presale'][str(utxo['amount'])]
        else:
            logger.error("NO PRICE MATCH: {}:{}".format(utxo['tx-hash'], utxo['amount']))
            continue

        if nfts_purchased == 13 and used_special == True:
            logger.error("Already used special price for self: {}:{}".format(utxo['tx-hash'], utxo['amount']))
            continue

        if nfts_purchased == 13:
            used_special = True

        logger.info('{}: {} lovelace, request mint {}'.format(utxo['tx-hash'], utxo['amount'], nfts_purchased))
        input_address = database.query_utxo_inputs(utxo['tx-hash'])[0]['address']
        stake_address = database.query_stake_address(input_address)

        for hodler in hodlers:
            if stake_address == hodler[0]:
                logger.info('{} HODL S1'.format(stake_address))
                for i in range(0, nfts_purchased):
                    if len(hodler[1]) > 0:
                        token = hodler[1].pop()
                        token_bonus = 0
                        if token.startswith('TCRx001x05x'):
                            token_bonus += 3
                        elif token.startswith('TCRx001x04x'):
                            token_bonus += 3
                        elif token.startswith('TCRx001x03x'):
                            token_bonus += 3
                        elif token.startswith('TCRx001x02x'):
                            token_bonus += 2
                        elif token.startswith('TCRx001x01x'):
                            token_bonus += 1

                        logger.info('{} = +{} BONUS'.format(token, token_bonus))
                        nfts_bonus += token_bonus

        logger.info("TOTAL Bonus: {}".format(nfts_bonus))
        total_purchased += nfts_purchased
        total_bonus += nfts_bonus
        nfts_total = nfts_purchased + nfts_bonus
        if nfts_total > 0:
            presale['whitelist'].append({"utxo-txid": utxo['tx-hash'],
                                         "utxo-txix": utxo['tx-ix'],
                                         "from-stake-addr": stake_address,
                                         "nfts": nfts_total})

    with open('nft/{}/{}/{}'.format(network, drop_name, output), 'w') as file:
        file.write(json.dumps(presale, indent=4))

    logger.info('Purchased = {}, Bonus = {}, Total = {}'.format(total_purchased, total_bonus, total_purchased + total_bonus))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
