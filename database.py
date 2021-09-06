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

from configparser import ConfigParser
import psycopg2

# https://github.com/input-output-hk/cardano-db-sync/blob/master/doc/interesting-queries.md
class Database:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_params = Database.read_config_params(self.config_file)
        self.connection = psycopg2.connect(**self.config_params)
        cursor = self.connection.cursor()
        cursor.execute('SELECT version()')
        db_version = cursor.fetchone()
        cursor.close()
        print('Postgres SQL Database Version: {}'.format(db_version))

    def close(self):
        self.connection.close()

    @staticmethod
    def read_config_params(filename):
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

        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        return row

    def query_total_supply(self):
        sql = '''select sum (value) / 1000000 as current_supply from tx_out as tx_outer where
                     not exists
                         ( select tx_out.id from tx_out inner join tx_in
                             on tx_out.tx_id = tx_in.tx_out_id and tx_out.index = tx_in.tx_out_index
                             where tx_outer.id = tx_out.id
                         );'''
        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        return row[0]

    def query_database_size(self):
        sql = 'select pg_size_pretty (pg_database_size (\'{}\'));'.format(self.config_params['database'])
        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        return row[0]

    def query_latest_slot(self):
        sql = 'select slot_no from block where block_no is not null order by block_no desc limit 1 ;'
        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        return int(row[0])

    def query_sync_progress(self):
        sql = '''select
                     100 * (extract (epoch from (max (time) at time zone 'UTC')) - extract (epoch from (min (time) at time zone 'UTC')))
                         / (extract (epoch from (now () at time zone 'UTC')) - extract (epoch from (min (time) at time zone 'UTC')))
                     as sync_percent from block ;'''
        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        return float(row[0])

    def query_tx_fee(self, txid):
        sql = 'select tx.id, tx.fee from tx where tx.hash = \'\\x{}\';'.format(txid)
        cursor = self.connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()
        return (row[0], int(row[1]))

    def query_utxo_outputs(self, txid):
        sql = 'select tx_out.* from tx_out inner join tx on tx_out.tx_id = tx.id where tx.hash = \'\\x{}\' ;'.format(txid)
        #print('sql = {}'.format(sql))
        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        outputs = []
        for row in rows:
            outputs.append({'address': row[3], 'value': int(row[7])})
        cursor.close()
        return outputs

    def query_utxo_inputs(self, txid):
        sql = 'select tx_out.* from tx_out inner join tx_in on tx_out.tx_id = tx_in.tx_out_id inner join tx on tx.id = tx_in.tx_in_id and tx_in.tx_out_index = tx_out.index where tx.hash = \'\\x{}\' ;'.format(txid)
        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        inputs = []
        for row in rows:
            inputs.append({'address': row[3], 'value': int(row[7])})
        cursor.close()
        return inputs