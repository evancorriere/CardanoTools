'''
criticalDataHelper.py
Author: Evan Corriere

DB helper script to log things as sold and track prices. 
'''

import sqlite3
import datetime

dbfilename = "/home/ec2-user/nfts-server/shared/nfts.db"
con = sqlite3.connect(dbfilename, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cur = con.cursor()

'''
nft management
'''
def set_minted(nftnum, recipient):
    # returns true on success
    if get_recipient(nftnum):
        raise Exception(f'{nftnum} already minted')

    try:
        cur.execute('BEGIN')
        cur.execute('UPDATE nfts SET minted=?, recipient=? WHERE nftnum=?', (True, recipient, nftnum))
        cur.execute('COMMIT')
        print(f'commited for {nftnum} and {recipient}')
        return True
    except:
        cur.execute('ROLLBACK')
        return False

def get_recipient(nftnum):
    cur.execute('SELECT recipient FROM nfts WHERE nftnum=?', [nftnum])
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return None

def get_recipient_threadsafe(nftnum):
    threadsafe_con = sqlite3.connect(dbfilename)
    threadsafe_cur = threadsafe_con.cursor()
    threadsafe_cur.execute('SELECT recipient FROM nfts WHERE nftnum=?', [nftnum])
    result = threadsafe_cur.fetchone()
    if result:
        return result[0]
    else:
        return None

def print_nfts_table():
    for row in cur.execute('SELECT * from nfts limit 10'):
        print(row)

def get_minted_count():
    cur.execute('SELECT COUNT(minted) from nfts where minted=?', [True])
    return cur.fetchone()[0]

def get_minted_count_threadsafe():
    threadsafe_con = sqlite3.connect(dbfilename)
    threadsafe_cur = threadsafe_con.cursor()
    threadsafe_cur.execute('SELECT COUNT(minted) from nfts where minted=?', [True])
    return threadsafe_cur.fetchone()[0]

def print_minted():
    cur.execute('SELECT nftnum, recipient from nfts where minted=?', [True])
    for res in cur.fetchall():
        print(res)

'''
Price management
'''

def set_price(price):
    try:
        time = datetime.datetime.now()
        cur.execute('BEGIN Transaction')
        cur.execute('UPDATE prices SET isCurrent=?, dateInvalidated=? WHERE isCurrent=?', (False, time, True))
        cur.execute('INSERT INTO prices VALUES (?, ?, NULL)', (price, True))
        cur.execute('COMMIT')
        return True
    except:
        cur.execute('ROLLBACK')
        return False

def get_current_price():
    cur.execute('SELECT price from prices where isCurrent=?', [True])
    return cur.fetchone()[0]

def get_current_price_threadsafe():
    threadsafe_con = sqlite3.connect(dbfilename)
    threadsafe_cur = threadsafe_con.cursor()
    threadsafe_cur.execute('SELECT price from prices where isCurrent=?', [True])
    return threadsafe_cur.fetchone()[0]

def print_prices_table():
    for row in cur.execute('SELECT * from prices'):
        print(row)

def check_price_valid(price, time):
    cur.execute('SELECT isCurrent, dateInvalidated FROM prices where price=?', [price])
    results = cur.fetchone()
    if not results:
        return False

    isCurrent, dateInvalidated = results
    if isCurrent:
        return True
    else:
        lastcall = dateInvalidated + datetime.timedelta(minutes=40)
        return lastcall > time

