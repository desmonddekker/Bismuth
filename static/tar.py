#this file is marginally dynamic, make sure you know what you run it against

import tarfile
import sys
import sqlite3
from decimal import *
from quantizer import *
import process_search

class Tar():
    def __init__(self):
        self.hdd = sqlite3.connect("ledger.db", timeout=1)
        self.hdd.text_factory = str
        self.h = self.hdd.cursor()

        self.hdd2 = sqlite3.connect("hyper.db", timeout=1)
        self.hdd2.text_factory = str
        self.h2 = self.hdd2.cursor()
        
        self.errors = 0
        
tar_obj = Tar()        

def dupes_check(cursor, name):
    print (f"Testing {name} for duplicates")

    cursor.execute("SELECT * FROM transactions WHERE signature IN (SELECT signature FROM transactions WHERE signature != '0' GROUP BY signature HAVING COUNT(*) >1)")
    results = cursor.fetchall()

    dupes_allowed = [708334,708335]

    for result in results:
        if result[0] not in dupes_allowed:
            print (f"Duplicate entry on block: {result}")
            tar_obj.errors += 1



def balance_from_cursor(cursor, address):
    credit = Decimal("0")
    debit = Decimal("0")
    for entry in cursor.execute("SELECT amount,reward FROM transactions WHERE recipient = ? ",(address, )):
        try:
            #result = cursor.fetchall()
            credit = credit + quantize_eight(entry[0]) + quantize_eight(entry[1])
            #print (result)
            credit = 0 if credit is None else credit
        except Exception as e:
            credit = 0
        #print (credit)


    for entry in cursor.execute("SELECT amount,fee FROM transactions WHERE address = ? ",(address, )):
        try:
            # result = cursor.fetchall()
            debit = debit + quantize_eight(entry[0]) + quantize_eight(entry[1])
            # print (result)
            debit = 0 if debit is None else debit
        except Exception as e:
            debit = 0
        # print (debit)

    return quantize_eight(credit-debit)

def balance_differences ():
    
    print ("Selecting all addresses from full ledger for errors")
    tar_obj.h.execute ("SELECT distinct(recipient) FROM transactions group by recipient;")
    addresses = tar_obj.h.fetchall ()

    for address in addresses:
        address = address[0]
        balance1 = balance_from_cursor(tar_obj.h, address)
        balance2 = balance_from_cursor(tar_obj.h2, address)
        if (balance1 == balance2):
            check = '  Ok'
        else:
            check = '> Ko'
            tar_obj.errors += 1

        if address.lower() != address or len(address) != 56 and (balance1 or balance2) != 0:
            print (f"{address} > wrong recipient")


        print(f"{check} {address} {balance1} {balance2}")

        if (Decimal(balance1) < 0 or Decimal(balance2) < 0):
            print(address,balance1,balance2)


    print(f"Done, {tar_obj.errors} errors.")

    if tar_obj.errors > 0:
        return_value = True
    else:
        return_value = False

    return return_value


dupes_check(tar_obj.h, "ledger")
dupes_check(tar_obj.h2, "hyperblocks")
balance_differences()


if tar_obj.errors > 0:
    print("There were errors, cannot continue")
    
else:

    if not process_search.proccess_presence ("node.py"):
        files = ["ledger.db-wal","ledger.db-shm","ledger.db","hyper.db-shm", "hyper.db-wal", "hyper.db", "index.db"]

        tar = tarfile.open("ledger.tar.gz", "w:gz")

        for file in files:
            try:
                print ("Compressing", file)
                tar.add(file, arcname=file)
            except:
                "Error compressing {}".format(file)

        print("Compression finished for", files)
        tar.close()

    else:
        print ("Node is running, cannot continue")

input("Press any key to continue")


