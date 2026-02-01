from datetime import datetime
import glob
import os
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class PortfolioData:
    positions: pd.DataFrame
    transactions: pd.DataFrame
    latest_date: pd.Timestamp
    unique_accounts: pd.DataFrame = field(init=False)

    def __post_init__(self):
        if self.positions is not None:
            self.unique_accounts = (
                self.positions[['Account Number', 'Account Name']]
                .drop_duplicates()
                .reset_index(drop=True)
            )

def load_data(data_dir):
    """
    Load the latest position file and all history files.
    Returns: positions_df, history_df
    """
    # 1. Load Positions
    pos_file, pos_date = get_latest_position_file(data_dir)
    print(f"Loading positions from: {pos_file} (Date: {pos_date.strftime('%Y-%m-%d')})")
    positions_df = pd.read_csv(pos_file, index_col=False)
    positions_df = clean_positions(positions_df)

    # 2. Load History
    transactions_df = load_transactions(data_dir)
    transactions_df = clean_transactions(transactions_df)
    
    return PortfolioData(positions_df, transactions_df, pos_date)


def get_latest_position_file(data_dir):
    """Find the latest Portfolio_Positions file based on the date in filename."""
    files = glob.glob(os.path.join(data_dir, 'Portfolio_Positions_*.csv'))
    if not files:
        raise FileNotFoundError("No Portfolio_Positions files found.")
    
    latest_file = None
    latest_date = None
    
    for f in files:
        basename = os.path.basename(f)
        date_part = basename.replace('Portfolio_Positions_', '').replace('.csv', '')
        try:
            date_obj = datetime.strptime(date_part, '%b-%d-%Y')
            if latest_date is None or date_obj > latest_date:
                latest_date = date_obj
                latest_file = f
        except ValueError:
            continue
    latest_date = pd.to_datetime(latest_date)
    return latest_file, latest_date

def clean_positions(positions_df):
    # Clean Position Columns
    positions_df.dropna(subset=['Account Name'], inplace=True)
    cols_to_clean = [
        'Last Price', 'Current Value', 'Cost Basis Total', 
        'Today\'s Gain/Loss Dollar', 'Total Gain/Loss Dollar'
    ]
    for col in cols_to_clean:
        if col in positions_df.columns:
            positions_df[col] = positions_df[col].apply(clean_currency)
    
    # Clean Quantity (remove match for formatting issues if any)
    if 'Quantity' in positions_df.columns:
         positions_df['Quantity'] = pd.to_numeric(positions_df['Quantity'], errors='coerce').fillna(0)
    positions_df['Asset Type'] = positions_df.apply(categorize_asset, axis=1) 
    return positions_df


def clean_currency(x):
    """
    Remove '$' and ',' from currency strings and convert to float.
    Handles '+$...' '-$...' and plain numbers.
    """
    if pd.isna(x) or x == '--' or x == '':
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    x = str(x).replace('$', '').replace(',', '').replace('%', '')
    # Handle negative signs explicitly if needed, though replace usually suffices for standard formats
    # Check for negative values represented as ($100)
    if '(' in x and ')' in x:
        x = x.replace('(', '-').replace(')', '')
    return float(x)


def load_transactions(data_dir, max_cols=14):
    hist_files = glob.glob(os.path.join(data_dir, 'Accounts_History_*.csv'))
    transactions_dfs = []
    print(f"Found {len(hist_files)} history files.")
    
    for f in hist_files:
        df = pd.read_csv(f, header=0, usecols=range(max_cols))
        transactions_dfs.append(df)

    transactions_df = pd.concat(transactions_dfs, ignore_index=True)
    return transactions_df
    
def clean_transactions(transactions_df):
    for col in transactions_df.columns:
        if (
            (transactions_df[col].dtype == 'object' ) or 
            (transactions_df[col].dtype == 'string')
        ):
            transactions_df[col] = transactions_df[col].str.strip()
    transactions_df['Run Date'] = pd.to_datetime(transactions_df['Run Date'], errors='coerce')
    if 'Settlement Date' in transactions_df.columns:
         transactions_df['Settlement Date'] = pd.to_datetime(transactions_df['Settlement Date'], errors='coerce')
    

    # Clean numeric columns
    transactions_numeric_cols = [
    'Amount ($)', 'Price ($)', 'Quantity', 
        'Commission ($)', 'Fees ($)', 'Accrued Interest ($)'
    ]
    for col in transactions_numeric_cols:
        if col in transactions_df.columns:
            transactions_df[col] = transactions_df[col].apply(clean_currency)
    transactions_df['Asset Type'] = transactions_df.apply(categorize_asset, axis=1) 

    # Fill symbol
    conditions = [
        transactions_df['Description'] == "FID BLUE CHIP GR K6",
        transactions_df['Description'] == "SP 500 INDEX PL CL E",
        transactions_df['Description'] == "SP 500 INDEX PL CL F"
    ]
    choices = ["FBCGX", "84679P173", "84679P173"]
    transactions_df['Symbol'] = np.select(conditions, choices, default=transactions_df.get('Symbol', None))
    
    # Sort by date
    transactions_df = transactions_df.sort_values('Run Date')
    return transactions_df

def categorize_asset(row):
    """
    Categorize asset into Stock, Bond, or Cash/MoneyMarket.
    """
    symbol = str(row['Symbol'])
    desc = str(row.get('Description', '')).upper()
    
    # Money Market Funds
    mmf_symbols = ['FZFXX', 'FDRXX', 'SPAXX', 'QUSBQ'] # QUSBQ is bank sweep
    if symbol in mmf_symbols or 'MONEY MARKET' in desc or 'CASH RESERVES' in desc or 'FDIC INSURED DEPOSIT' in desc:
        return 'Cash'
    
    # US Treasury Bills/Notes
    # CUSIPs usually 9 digits, often starting with 912...
    # Or description contains TREAS BILL
    if (len(symbol) >= 8 and symbol.startswith('912')) or 'TREAS BILL' in desc or 'TREASURY BILL' in desc:
        return 'Bond'
        
    # Default to Stock/ETF
    return 'Stock'


if __name__ == "__main__":
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    output_dir = f'{project_path}/output'

    data = load_data(data_dir)
    print(data.positions.head())