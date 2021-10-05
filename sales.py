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
File: sales.py
Author: Kris Henderson
"""

from typing import List

import json
import time
from datetime import datetime

class Sales:
    """
    Simple class to track each sale as JSON file
    """
    def __init__(self, network: str, drop: str):
        self.filename = 'nft/{}/{}/sales.json'.format(network, drop)
        self.sales = {'transactions': []}
        try:
            with open(self.filename, 'r') as file:
                self.sales = json.load(file)
        except FileNotFoundError as e:
            pass

    def contains(self, hash: str, ix: str) -> bool:
        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                return True

        return False

    def add_utxo(self, hash: str, ix: str, amount: int, count: int) -> bool:
        if self.contains(hash, ix):
            return False

        self.sales['transactions'].append({'input-hash': hash,
                                           'input-ix': ix,
                                           'input-amount': amount,
                                           'count': count,
                                           'time': {'epoch': round(time.time()),
                                                    'date-time': datetime.now().strftime("%Y/%m/%d %H:%M:%S")}
                                          })
        return True

    def remove_utxo(self, hash: str, ix: str) -> bool:
        if not self.contains(hash, ix):
            return False

        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                self.sales['transactions'].remove(item)
                return True

        return False

    def set_input_address(self, hash: str, ix: str, address: str) -> bool:
        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                item['input-address'] = address
                return True

        return False

    def set_tx_ada(self, hash: str, ix: str, out_min_ada: int) -> bool:
        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                item['out-ada'] = out_min_ada
                return True

        return False

    def set_refund(self, hash: str, ix: str, fee: int, amount: int) -> bool:
        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                item['refund'] = {'amount': amount, 'fee': fee}
                return True

        return False

    def set_output_txid(self, hash: str, ix: str, txid: str) -> bool:
        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                item['out-txid'] = txid
                return True

        return False

    def set_tokens_minted(self, hash: str, ix: str, tokens: List) -> bool:
        for item in self.sales['transactions']:
            if item['input-hash'] == hash and item['input-ix'] == ix:
                item['tokens-minted'] = tokens
                return True

        return False

    def commit(self) -> None:
        with open(self.filename, 'w') as file:
            file.write(json.dumps(self.sales, indent=4))
