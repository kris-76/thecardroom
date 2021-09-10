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

class Sales:
    """
    Simple class to track each sale as JSON file
    """
    def __init__(self, network: str):
        self.filename = 'nft/{}/sales.json'.format(network)
        self.sales = {'transactions': []}
        try:
            with open(self.filename, 'r') as file:
                self.sales = json.load(file)
        except FileNotFoundError as e:
            pass

        self.input_hash = None
        self.input_amount = 0
        self.input_address = None
        self.num_nfts = 0
        self.tokens_purchased = None
        self.timeout = False
        self.output_hash = None
        self.refund_fee = 0
        self.refund_amount = 0

    def set_input_utxo(self, hash: str, amount: int) -> None:
        self.input_hash = hash
        self.input_amount = amount

    def set_purchase_amount(self, num_nfts: int) -> None:
        self.num_nfts = num_nfts

    def set_input_address(self, address: str) -> None:
        self.input_address = address

    def set_tokens_purchased(self, tokens: List[str]) -> None:
        self.tokens_purchased = tokens

    def set_timeout(self, timeout: bool) -> None:
        self.timeout = timeout

    def set_output_utxo(self, hash: str) -> None:
        self.output_hash = hash

    def set_refund(self, fee: int, amount: int) -> None:
        self.refund_fee = fee
        self.refund_amount = amount


    def commit(self) -> None:
        tx = {
            'tx-time': round(time.time()),
            'input-hash': self.input_hash,
            'input-amount': self.input_amount,
            'input-address': self.input_address,
            'num-nfts': self.num_nfts,
            'tokens-purchased': self.tokens_purchased,
            'timeout': self.timeout,
            'output-hash': self.output_hash,
            'refund-fee': self.refund_fee,
            'refund-amount': self.refund_amount
        }

        self.sales['transactions'].append(tx)
        with open(self.filename, 'w') as file:
            file.write(json.dumps(self.sales, indent=4))

        self.input_hash = None
        self.input_amount = 0
        self.input_address = None
        self.num_nfts = 0
        self.tokens_purchased = None
        self.timeout = False
        self.output_hash = None
        self.refund_fee = 0
        self.refund_amount = 0
