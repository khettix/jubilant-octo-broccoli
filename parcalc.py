#! python3


import sys
import os
import csv
from collections import defaultdict
# ^dict subclass that calls a factory function to insert 0 for missing values
import pandas as pd


# =============================================================================
# START SELECTION GROUP (1)
# =============================================================================


def file_name():
    while True:
        global fileName  # <crude. make fxn return var instead
        fileName = input('\nfile name: ')
        if os.path.exists(fileName + '.csv') is False:
            print('\nfile does not exist')
            continue
        if os.path.exists(fileName + '.csv') is True:
            break
    select_report()


def select_report():
    reportType = input('\npyxis, dbextract, or merge only? ')

    if reportType == 'pyxis':
        par_pyxis(vend_dict_pyxis(), timespan())
        # For pulling MedDescription, Quantity from AuditTransactionDetail.csv
        # (filtering for station name and transaction type vend) then sending
        # these results into a dictionary merging each MedDescription key and
        # performing summation on each med's vend Quantity then writing
        # these values to a new csv file.
    elif reportType == 'dbextract':
        par_dbextract(charge_dict_dbextract(), timespan())
    elif reportType == 'merge only':
        merge_only()
    else:
        print('\ninvalid response')
        select_report()


def timespan():
    while True:
        try:
            days = int(input('\nnumber of days: '))
            if type(days) is not int:
                raise ValueError()
            break  # will only execute if the exception isn't raised
        except ValueError:
            print('\ninvalid input')
    return days

# =============================================================================
# START PYXIS GROUP (2.1)
# =============================================================================


def vend_dict_pyxis():
    reader = csv.DictReader(open(fileName + '.csv', newline=''))
    meds = defaultdict(int)
    # setting default_factory attribute to int
    # makes defaultdict useful for counting
    for row in reader:
        meds[row["MedDescription"].lower()] += float(row["Quantity"])
    return meds


def par_pyxis(meds, days):
    # idea is to refill q7d and min qty covers 3d, so 7d par is 10d
    fourteenPar = days/14
    sevenPar = days/10
    minQty = days/3

    with open(fileName + '_output.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Item", "Total", "14d Par", "7d Par", "Min"])
        # .items() method iterates over each key/value pair
        # in the dict 'meds' for minimal memory usage
        for key, val in meds.items():
            writer.writerow([key, val, round(val/fourteenPar),
                             round(val/sevenPar), round(val/minQty)])

    script_complete_msg('pyxis')


# =============================================================================
# START DBEXTRACT GROUP (2.2)
# =============================================================================


def charge_dict_dbextract():
    reader = csv.DictReader(open(fileName + '.csv', newline=''))
    meds = defaultdict(int)

    for row in reader:
        meds[row["NDC"]] += float(row["Count"])  # why did I make this a float?
    return meds


def par_dbextract(meds, days):
    fourteenPar = days/14
    sevenPar = days/10
    threePar = days/3

    with open(fileName + '_output.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Item", "Total", "14d Par", "7d Par", "3d Min"])

        # .items() iterates over each key/value pair in the dict 'meds'
        for key, val in meds.items():
            writer.writerow([key, val, round(val/fourteenPar),
                             round(val/sevenPar), round(val/threePar)])

    merge_name_ndc()


def merge_name_ndc():
    # This function uses the output from ORDERF013/RXDISPP (dispenses)
    # and ORDERF013/RXFORXAUD (only need fxgenname and fxndc columns) to
    # attach a med name to each NDC. Name each csv file accordingly before
    # running.
    # Find a way to push this into a dict so dictreader can combine duplicate
    # med name rows, handling the numbers each iteration.
    # ^solved for now using pivot table
    a = pd.read_csv('formularyExtract.csv')
    b = pd.read_csv('dispense_output.csv')
    merged = a.merge(b, on='Item')
    merged.to_csv('dispense_final.csv', index=False)

    os.unlink('dispense_output.csv')

    script_complete_msg('dbextract')


# =============================================================================
# START MERGE ONLY (2.3)
# =============================================================================


def merge_only():
    a = pd.read_csv('formularyExtract.csv')
    b = pd.read_csv(fileName + '.csv')
    merged = a.merge(b, on="Item")
    merged.to_csv(fileName + '_merged.csv', index=False)

    script_complete_msg('merge_only')


# =============================================================================
# START OUTPUT MESSAGE (3)
# =============================================================================


def script_complete_msg(report):
    if report == 'pyxis':
        print('\nOutput file \'' + fileName + '_output.csv\' ' +
              'generated.\n')
    elif report == 'dbextract':
        print('\nOutput file \'dispense_final.csv\' generated.\n')
    elif report == 'merge_only':
        print('\nOutput file \'' + fileName + '_merged.csv\' ' +
              'generated.\n')
    else:
        print('An error has occured.')


# =============================================================================


def main():
    r = input('Continue to run script (Y/N)? ')
    if r.lower() == 'y':
        file_name()
    else:
        pass


# Check here first if script seems fucked
os.chdir('C:\\Scripts\\parcalc\\current')


print("""
-files must be located in C:\\Scripts\\parcalc\\current
-for Pyxis option, ensure columns are named MedDescription & Quantity
-for dbextract, file name must be dispense and columns are NDC & Count
-for merge only, ndc column must be named Item\n""")


main()
