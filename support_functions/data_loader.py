from datetime import datetime
import glob
import os
import pandas as pd




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
    
    return positions_df, transactions_df, pos_date


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


def load_transactions(data_dir):
    hist_files = glob.glob(os.path.join(data_dir, 'Accounts_History_*.csv'))
    transactions_dfs = []
    print(f"Found {len(hist_files)} history files.")
    
    for f in hist_files:
        df = pd.read_csv(f, on_bad_lines='skip') 
        transactions_dfs.append(df)

    transactions_df = pd.concat(transactions_dfs, ignore_index=True)
    return transactions_df
    
def clean_transactions(transactions_df):
    # remove space in the beginning of column
    for col in transactions_df.columns:
        if (
            (transactions_df[col].dtype == 'object' ) or 
            (transactions_df[col].dtype == 'string')
        ):
            transactions_df[col] = transactions_df[col].str.strip()   
    # Standardize dates
    transactions_df['Run Date'] = pd.to_datetime(transactions_df['Run Date'], errors='coerce')
    # Sometimes 'Settlement Date' exists
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
        
    # Sort by date
    transactions_df = transactions_df.sort_values('Run Date')
    return transactions_df
