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
File: database.py
Author: Kris Henderson
"""

from typing import Dict
from configparser import ConfigParser
import psycopg2
import logging
import binascii

logger = logging.getLogger('database')

# https://github.com/input-output-hk/cardano-db-sync/blob/master/doc/interesting-queries.md
class Database:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config_params = Database.read_config_params(self.config_file)
        self.connection = psycopg2.connect(**self.config_params)
        cursor = self.connection.cursor()
        cursor.execute('SELECT version()')
        db_version = cursor.fetchone()
        cursor.close()
        logger.debug('Postgres SQL Database Version: {}'.format(db_version))

    def close(self):
        self.connection.close()

    @staticmethod
    def read_config_params(filename: str):
        section='postgresql'
        parser = ConfigParser()
        parser.read(filename)

        config_params = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                config_params[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return config_params

    def query_chain_metadata(self):
        sql = 'select * from meta;'
        logger.debug('query_chain_metadata(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_chain_metadata(), response:\r\n{}'.format(row))
        cursor.close()
        return row

    def query_total_supply(self):
        sql = ('select sum (value) / 1000000 as current_supply from tx_out as tx_outer where '
               '      not exists '
               '          ( select tx_out.id from tx_out inner join tx_in '
               '              on tx_out.tx_id = tx_in.tx_out_id and tx_out.index = tx_in.tx_out_index '
               '              where tx_outer.id = tx_out.id '
               '          );')
        logger.debug('query_total_supply(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_total_supply(), response:\r\n{}'.format(row))
        cursor.close()
        return row[0]

    def query_database_size(self):
        sql = 'select pg_size_pretty (pg_database_size (\'{}\'));'.format(self.config_params['database'])
        logger.debug('query_database_size(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_database_size(), response:\r\n{}'.format(row))
        cursor.close()
        return row[0]

    def query_latest_slot(self):
        sql = ('select slot_no from block '
               'where block_no is not null '
               'order by block_no desc limit 1;')
        logger.debug('query_latest_slot(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_latest_slot(), response:\r\n{}'.format(row))
        cursor.close()
        return int(row[0])

    def query_sync_progress(self):
        sql = '''select
                     100 * (extract (epoch from (max (time) at time zone 'UTC')) - extract (epoch from (min (time) at time zone 'UTC')))
                         / (extract (epoch from (now () at time zone 'UTC')) - extract (epoch from (min (time) at time zone 'UTC')))
                     as sync_percent from block ;'''
        logger.debug('query_sync_progress(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_sync_progress(), response:\r\n{}'.format(row))
        cursor.close()
        return float(row[0])

    def query_tx_fee(self, txid: str):
        sql = 'select tx.id, tx.fee from tx where tx.hash = \'\\x{}\';'.format(txid)
        logger.debug('query_tx_fee(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_tx_fee(), response:\r\n{}'.format(row))
        cursor.close()
        return (row[0], int(row[1]))

    def query_stake_address(self, address: str):
        sql = ('select stake_address.id as stake_address_id, tx_out.address, stake_address.view as stake_address '
               'from tx_out inner join stake_address on tx_out.stake_address_id = stake_address.id '
               'where address = \'{}\';'.format(address))

        logger.debug('query_stake_address(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        logger.debug('query_stake_address(), response:\r\n{}'.format(row))
        cursor.close()
        return row[2]

    def query_utxo_outputs(self, txid: str):
        sql = ('select tx_out.* from tx_out '
               'inner join tx on tx_out.tx_id = tx.id '
               'where tx.hash = \'\\x{}\';'.format(txid))
        logger.debug('query_utxo_outputs(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        logger.debug('query_utxo_outputs(), response:\r\n{}'.format(rows))
        outputs = []
        for row in rows:
            outputs.append({'address': row[3], 'value': int(row[7])})
        cursor.close()
        return outputs

    def query_utxo_inputs(self, txid: str):
        sql = ('select tx_out.* from tx_out '
               'inner join tx_in on tx_out.tx_id = tx_in.tx_out_id '
               'inner join tx    on tx.id = tx_in.tx_in_id and tx_in.tx_out_index = tx_out.index '
               'where tx.hash = \'\\x{}\';'.format(txid))
        logger.debug('query_utxo_inputs(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        logger.debug('query_utxo_inputs(), response:\r\n{}'.format(rows))
        inputs = []
        for row in rows:
            inputs.append({'address': row[3], 'value': int(row[7])})
        cursor.close()
        return inputs

    def query_txhash_time(self, txhash: str):
        sql = ('select block.time, block.slot_no from tx '
               'inner join block on tx.block_id = block.id '
               'where tx.hash = \'\\x{}\';'.format(txhash))
        logger.debug('query_txhash_time(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        return (row[0], row[1])

    def query_mint_transactions(self, policy_id: str) -> Dict:
        sql = 'select * from ma_tx_mint where ma_tx_mint.policy=\'\\x{}\' order by tx_id;'.format(policy_id)
        logger.debug('query_mint_transactions(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        tokens = {}
        for row in rows:
            name = binascii.unhexlify(bytes(row[2]).hex()).decode("utf-8")
            quantity = row[3]
            if not name in tokens:
                tokens[name] = quantity
            else:
                tokens[name] += quantity

            if tokens[name] < 0:
                logger.error('that was unexpected.  need to sort by date???')
                raise Exception('that was unexpected.  need to sort by date???')

            if tokens[name] == 0:
                tokens.pop(name)

        return tokens

    # https://github.com/input-output-hk/cardano-db-sync/blob/master/doc/schema.md
    def query_current_owner(self, policy_id: str):
        def sort_by_time(item):
            return item['time']

        sql = ('select ma_tx_out.name, stake_address.view, block.slot_no from ma_tx_out '
               'inner join tx_out on ma_tx_out.tx_out_id = tx_out.id '
               'inner join tx on tx_out.tx_id = tx.id '
               'inner join block on tx.block_id = block.id '
               'inner join stake_address on tx_out.stake_address_id = stake_address.id '
               'where ma_tx_out.policy=\'\\x{}\';'.format(policy_id))
        logger.debug('query_current_owner(), sql = {}'.format(sql))

        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        tokens = {}
        for row in rows:
            name = binascii.unhexlify(bytes(row[0]).hex()).decode("utf-8")
            if name in tokens:
                if tokens[name]['slot'] < row[2]:
                    tokens[name]['address'] = row[1]
                    tokens[name]['slot'] = row[2]
            else:
                tokens[name] = {'address': row[1], 'slot': row[2]}

        return tokens
