import pandas as pd
import os
import glob
from datetime import datetime


def load_position(data_folder_path, position_file_pattern):
    position_file = _gather_position_files(data_folder_path, position_file_pattern)

    if not position_file is None:
        position = pd.read_csv(position_file)
        position = _clean_position(position)
    else:
        print("No position file found.")
    return position

def _gather_position_files(data_folder_path, position_file_pattern):
    position_file_path_pattern = os.path.join(data_folder_path, position_file_pattern)
    position_files = glob.glob(position_file_path_pattern)
    position_file = _find_latest_position_file(position_files)
    return position_file


def _find_latest_position_file(position_files):
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


def _clean_position(position):
    position = _remove_NA_value(position,"Current Value")
    position = _transfer_dollar_to_float(position, "Current Value")
    position = _transfer_dollar_to_float(position, "Cost Basis Total")
    return position


def _transfer_dollar_to_float(df, colNames):
    """
    Change "$123,456" to 123456.0, and "--" to 0.0
    """
    df_copy = df.copy()
    # Replace any "--" with "$0"
    cleaned = df_copy[colNames].str.replace("--", "$0", regex=False)
    # Remove dollar sign and commas, then convert to float
    cleaned = cleaned.str.replace("$", "", regex=False).str.replace(",", "", regex=False)
    df_copy[colNames] = cleaned.astype(float)
    return df_copy


def load_transaction(data_folder_path, transaction_file_pattern):
    transaction_files = _gather_transaction_files(data_folder_path,transaction_file_pattern)
    transactions = _combine_transaction_files(transaction_files)
    transactions = _clean_transactions(transactions)
    print(f"The latest transaction date is {transactions['Run Date'].max()}")
    return transactions


def _gather_transaction_files(data_folder_path,transaction_file_pattern):
    transaction_file_path_pattern = os.path.join(
        data_folder_path, transaction_file_pattern
    )
    transaction_files = glob.glob(transaction_file_path_pattern)
    return transaction_files

def _combine_transaction_files(transaction_files):
    transaction_list = [
        pd.read_csv(file, usecols=range(14)) for file in transaction_files
    ]
    transactions = pd.concat(transaction_list, ignore_index=True)
    return transactions

def _remove_NA_value(df,colName):
    df_copy = df.copy()
    df_copy = df_copy[
        df_copy[colName].notna()
    ] 
    return df_copy

def _remove_leading_space(df,colName):
    df_copy = df.copy()
    df_copy[colName] = df_copy[colName].str.lstrip()
    return df_copy

def _str_to_date(df, colName, format):
    df_copy = df.copy()
    df_copy[colName] = pd.to_datetime(
        df_copy[colName], format=format
    ).dt.date
    return df_copy

def _add_Transfer_symbol(df):
    df_copy = df.copy()
    df_copy.loc[df_copy["Symbol"] == "  ", "Symbol"] = "Transfer"
    return df_copy

def _sort_df_by_column(df, colName):
    df_copy = df.copy()
    df_copy = df_copy.sort_values(by=colName).reset_index(
        drop=True
    )
    return df_copy


def _clean_transactions(transactions):
    transactions = _remove_NA_value(transactions,"Amount ($)")
    transactions = _remove_leading_space(transactions,"Run Date")
    transactions = _str_to_date(transactions,"Run Date","%m/%d/%Y")
    transactions = _str_to_date(transactions,"Settlement Date","%m/%d/%Y")
    transactions = _add_Transfer_symbol(transactions)
    transactions = _remove_leading_space(transactions,"Symbol")
    transactions = _remove_leading_space(transactions,"Description")
    transactions = _sort_df_by_column(transactions,"Run Date")
    return transactions
