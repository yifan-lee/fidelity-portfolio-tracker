import pandas as pd
import os
import glob
from datetime import datetime


def load_position(data_folder_path, position_file_pattern):

    position = None
    position_file_path_pattern = os.path.join(data_folder_path, position_file_pattern)
    position_files = glob.glob(position_file_path_pattern)
    position_file = find_latest_position_file(position_files)

    if not position_file is None:
        position = pd.read_csv(position_file)
        position = clean_position(position)
    else:
        print("No position file found.")
    return position


def find_latest_position_file(position_files):
    latest_file = None
    latest_date = None

    for file_path in position_files:
        file_name = os.path.basename(file_path)
        date_str = file_name.split("_")[-1].replace(".csv", "")
        file_date = datetime.strptime(date_str, "%b-%d-%Y")

        if latest_date is None or file_date > latest_date:
            latest_date = file_date
            latest_file = file_path

    return latest_file


def clean_position(position):
    position_copy = position.copy()
    position_copy = position_copy[
        position_copy["Current Value"].notna()
    ]  # remove rows without current value
    position_copy["Current Value"] = transfer_dollar_to_float(
        position_copy["Current Value"]
    )
    position_copy["Cost Basis Total"] = transfer_dollar_to_float(
        position_copy["Cost Basis Total"]
    )
    return position_copy


def load_transaction(data_folder_path, transaction_file_pattern):
    transaction_file_path_pattern = os.path.join(
        data_folder_path, transaction_file_pattern
    )
    transaction_files = glob.glob(transaction_file_path_pattern)

    transactions = combine_transaction_files(transaction_files)
    transactions = clean_transactions(transactions)
    print(f"The latest transaction date is {transactions['Run Date'].max()}")
    return transactions


def combine_transaction_files(transaction_files):
    transaction_list = [
        pd.read_csv(file, usecols=range(14)) for file in transaction_files
    ]
    transactions = pd.concat(transaction_list, ignore_index=True)
    return transactions


def clean_transactions(transactions):
    transactions_copy = transactions.copy()
    transactions_copy = transactions_copy[
        transactions_copy["Amount ($)"].notna()
    ]  # remove rows without  value
    transactions_copy["Run Date"] = pd.to_datetime(
        transactions_copy["Run Date"], format=" %m/%d/%Y"
    ).dt.date
    transactions_copy["Settlement Date"] = pd.to_datetime(
        transactions_copy["Settlement Date"], format="%m/%d/%Y"
    ).dt.date
    transactions_copy.loc[transactions_copy["Symbol"] == "  ", "Symbol"] = "Transfer"
    transactions_copy["Symbol"] = transactions_copy[
        "Symbol"
    ].str.lstrip()  # remove space at the beginning of Symbol
    transactions_copy = transactions_copy.sort_values(by="Run Date").reset_index(
        drop=True
    )
    return transactions_copy


def transfer_dollar_to_float(dat):
    """
    Change "$123,456" to 123456.0, and "--" to 0.0
    """
    # Replace any "--" with "$0"
    cleaned = dat.str.replace("--", "$0", regex=False)
    # Remove dollar sign and commas, then convert to float
    cleaned = cleaned.str.replace("$", "", regex=False).str.replace(",", "", regex=False)
    return cleaned.astype(float)
