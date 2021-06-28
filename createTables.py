'''
createTables.py
Author: Evan Corriere

Creates tables used by criticalDataHelper.py
'''


import sqlite3

TOTAL_NFTS = 12500
con = sqlite3.connect('/home/ec2-user/nfts-server/shared/nfts.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
cur = con.cursor()

# Setup price table
def createPricesTable():
    cur.execute('DROP TABLE IF EXISTS prices')
    cur.execute('CREATE TABLE prices (price int PRIMARY KEY, isCurrent boolean, dateInvalidated timestamp)')
    cur.execute('INSERT INTO prices VALUES (?, ?, NULL)', (7000000, True))
    con.commit()


def createNftsTable():
    cur.execute('DROP TABLE IF EXISTS nfts')
    cur.execute('CREATE TABLE nfts (nftnum int PRIMARY KEY, minted boolean, recipient text)')
    nft_values = [(i, False) for i in range(1, TOTAL_NFTS + 1)]
    cur.executemany('INSERT INTO nfts VALUES (?, ?, NULL)', nft_values)
    con.commit()

def printPricesTable():
    print('********** PRICES **********')
    for row in cur.execute('SELECT * from prices'):
        print(row)


def printNftsTable():
    print('********** NFTS **********')
    for row in cur.execute('Select * from nfts limit 10'):
        print(row)


createPricesTable()
createNftsTable()

printPricesTable()
printNftsTable()






