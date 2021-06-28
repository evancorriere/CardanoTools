'''
processTransactions.py
Author: Evan Corriere

This script it meant to automate the NFT purchasing flow by repeatedly checking for UTXOs and 
responding by sending customers NFTs. critialDataHelper.py is used to log prices and what is sold, while 
Transaction.py builds and submits transactions. 

Once 1000 NFTs are sold, the price increased by 5 ADA. 
'''

import subprocess
import traceback
import requests
from Transaction import Transaction
import time
import os, sys
import numpy as np
import json
import pickle
import datetime
import criticalDataHelper as cdh
import logging

logging.basicConfig(filename='server.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

TOTAL_NFTS = 12500
SAVINGS_ADDRESS = 'REDACTED' # where leftover ada should be sent 
PUBLIC_ADDRESS = 'REDACTED' # where customers will send funds
SLEEP_TIME = 120 
NETWORK_ARGS = ['--mainnet']
#NETWORK_ARGS = ['--testnet-magic', '1097911063']
HEADERS = {'project_id': 'REDACTED'}
ONE_ADA = 1000000
MINT_ORDER = np.arange(1, TOTAL_NFTS + 1)
np.random.default_rng(seed=9999).shuffle(MINT_ORDER) # not the actual seed used in Adaboys
os.environ['CARDANO_NODE_SOCKET_PATH'] = '/home/ec2-user/node/sockets/node.socket'


def get_mint_index():
    with open('current_index.txt', 'rb') as file:
        return pickle.load(file)

def set_mint_index(index):
    with open('current_index.txt', 'wb') as file:
        pickle.dump(index, file)

def getTxSource(txHash):
    # returns address that send ada in tx txHash
    try:
        url = f'https://cardano-mainnet.blockfrost.io/api/v0/txs/{txHash}/utxos'
        jsonResponse = requests.get(url, headers=HEADERS).json()
        return jsonResponse['inputs'][0]['address']
    except Exception as e:
        logging.warning(f'Problem with blockfrost query for {txHash}\n,\t {e}')

def updateNftName(nftnum, name):
    with open(f'metadata/nft{name}.json', 'r') as infile:
        metadata = json.load(infile)
        
    metadata['721']['policyhash'][f'nft{nftnum}']['nickname'] = name
    with open(f'metadata/nft{name}.json', 'w') as outfile:
        json.dump(metadata, outfile, indent=4)

def process_utxos():
    mint_index = get_mint_index()
    cmd = ["cardano-cli", "query", "utxo", "--address",  PUBLIC_ADDRESS] + NETWORK_ARGS
    utxoResults = subprocess.run(cmd, stdout=subprocess.PIPE)
    currentTime = datetime.datetime.now()
    currentPrice = cdh.get_current_price()

    for row in utxoResults.stdout.decode('utf-8').split("\n")[2:-1]:
        changedDB = False
        increasedIndex = False
        submitted = False
        try:
            nftnum = int(MINT_ORDER[mint_index])
            split_row = row.split()
            txHash = split_row[0]
            txIx = split_row[1]
            txLovelace = int(split_row[2])

            if cdh.check_price_valid(txLovelace, currentTime) or txLovelace > currentPrice:
                logging.info(f'Attempting to process {txHash} and nft#{nftnum}')
                sendbackAmount = int(1.5 * ONE_ADA)
            
                if txLovelace > currentPrice:
                    sendbackAmount += txLovelace - currentPrice
                    logging.info(f'Overpayed: setting sendback amount to {sendbackAmount}')

                senderAddr = getTxSource(txHash)
                if not senderAddr:
                    continue
                transaction = Transaction(txHash, txIx, txLovelace, senderAddr, sendbackAmount, SAVINGS_ADDRESS, nftnum)
                changedDB = True
                if not cdh.set_minted(nftnum, senderAddr):
                    raise Exception('set minted failed')
                logging.info(f'Logged {nftnum} as minted')
                mint_index += 1
                set_mint_index(mint_index)
                increasedIndex = True
                if mint_index != 0 and mint_index % 1000 == 0:
                    curr_price = cdh.get_current_price()
                    new_price = curr_price + int(ONE_ADA * 5)
                    cdh.set_price(new_price)
                    logging.info('Raising price from {curr_price} to {new_price}')
                transaction.build_sign_submit()
                submitted = True
                logging.info('Submit - success')
                print(f'minted nft {nftnum}')
            else:
                logging.info(f'invalid amount from {txHash}')
        except Exception as e:
            logging.warning(f'Exception when processing mint index {mint_index}, {txHash}, {e}')
            if changedDB and not submitted and not increasedIndex:
                # perhaps something is wrong with this index
                logging.warning(f'Skipping index {mint_index}')
                mint_index += 1
                set_mint_index(mint_index)
                if mint_index != 0 and mint_index % 1000 == 0:
                    curr_price = cdh.get_current_price()
                    new_price = curr_price + int(ONE_ADA * 5)
                    cdh.set_price(new_price)
                    logging.info('Raising price from {curr_price} to {new_price}')

currind = get_mint_index()
currprice = cdh.get_current_price()
logging.info(f'Starting to check transaction: curr index = {currind} and curr price = {currprice}')

while True:
    print('checking UTXOS')
    process_utxos()
    time.sleep(SLEEP_TIME)

