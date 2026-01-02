import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import optimize

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

def parse_date(date_str):
    """Parse various date formats."""
    if pd.isna(date_str):
        return None
    try:
        return pd.to_datetime(date_str).normalize()
    except Exception:
        return None

def get_latest_position_file(data_dir):
    """Find the latest Portfolio_Positions file based on the date in filename."""
    files = glob.glob(os.path.join(data_dir, 'Portfolio_Positions_*.csv'))
    if not files:
        raise FileNotFoundError("No Portfolio_Positions files found.")
    
    # Parse dates from filenames: Portfolio_Positions_MMM-DD-YYYY.csv
    # Example: Portfolio_Positions_Dec-31-2025.csv
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

def load_data(data_dir):
    """
    Load the latest position file and all history files.
    Returns: positions_df, history_df
    """
    # 1. Load Positions
    pos_file, pos_date = get_latest_position_file(data_dir)
    print(f"Loading positions from: {pos_file} (Date: {pos_date.strftime('%Y-%m-%d')})")
    
    # Read position file. Skip rows that are just explanatory text if any (usually header handles it)
    # Based on inspection, the file has a header row.
    # Data rows have a trailing comma but header does not, causing pandas to shift columns.
    # We can fix this by reading with index_col=False, but specifically for this mismatch case:
    # If we use engine='python', we can use generic handling.
    # Or simplified: if row has extra comma, it creates an unnamed column at the end if we don't treat first col as index.
    # Better approach: Read header, then read data, ensure column count matches.
    
    try:
        # Try reading with skipping the potential issue or explicitly setting names if needed.
        # But simpler fix for "Header N, Data N+1" is index_col=False usually works? 
        # Actually with N+1 data, pandas thinks col 1 is index.
        positions_df = pd.read_csv(pos_file, index_col=False)
        
        # Check if the last column is unnamed (from trailing comma) and drop it
        if positions_df.columns[-1].startswith('Unnamed'):
             positions_df = positions_df.iloc[:, :-1]
             
    except Exception:
        # Fallback
        positions_df = pd.read_csv(pos_file)

    # Clean Position Columns
    cols_to_clean = ['Last Price', 'Current Value', 'Cost Basis Total', 'Today\'s Gain/Loss Dollar', 'Total Gain/Loss Dollar']
    for col in cols_to_clean:
        if col in positions_df.columns:
            positions_df[col] = positions_df[col].apply(clean_currency)
    
    # Clean Quantity (remove match for formatting issues if any)
    if 'Quantity' in positions_df.columns:
         positions_df['Quantity'] = pd.to_numeric(positions_df['Quantity'], errors='coerce').fillna(0)

    # 2. Load History
    hist_files = glob.glob(os.path.join(data_dir, 'Accounts_History_*.csv'))
    history_dfs = []
    print(f"Found {len(hist_files)} history files.")
    
    for f in hist_files:
        # History files start with "Run Date,Account,..." but sometimes have empty lines at top?
        # Use python engine for more robust handling of quotes and separators
        try:
            df = pd.read_csv(f, on_bad_lines='skip') 
        except Exception as e:
            print(f"Warning: Failed to read {f} with default settings. Retrying with flexible parsing. Error: {e}")
            try:
                # Sometimes header is on a different line or there's metadata at the top
                # Let's try to detect header
                with open(f, 'r') as tmp_f:
                    lines = tmp_f.readlines()
                
                header_row = 0
                for i, line in enumerate(lines[:20]):
                    if "Run Date" in line and "Account" in line:
                        header_row = i
                        break
                
                df = pd.read_csv(f, header=header_row, on_bad_lines='skip')
            except Exception as e2:
                print(f"Error reading {f}: {e2}")
                continue
                
        history_dfs.append(df)
    
    if history_dfs:
        history_df = pd.concat(history_dfs, ignore_index=True)
    else:
        history_df = pd.DataFrame()
        
    # Clean History Columns
    if not history_df.empty:
        # Standardize dates
        history_df['Run Date'] = pd.to_datetime(history_df['Run Date'], errors='coerce')
        # Sometimes 'Settlement Date' exists
        if 'Settlement Date' in history_df.columns:
             history_df['Settlement Date'] = pd.to_datetime(history_df['Settlement Date'], errors='coerce')
        
        # Clean numeric columns
        hist_numeric_cols = ['Amount ($)', 'Price ($)', 'Quantity', 'Commission ($)', 'Fees ($)', 'Accrued Interest ($)']
        for col in hist_numeric_cols:
            if col in history_df.columns:
                history_df[col] = history_df[col].apply(clean_currency)
        
        # Sort by date
        history_df = history_df.sort_values('Run Date')
        
    return positions_df, history_df

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

def xirr(cash_flows):
    """
    Calculate Internal Rate of Return (XIRR).
    cash_flows: List of (date, amount) tuples.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None
        
    dates, amounts = width = zip(*cash_flows)
    
    # Convert dates to days from start
    min_date = min(dates)
    days = [(d - min_date).days for d in dates]
    
    # Optimization function
    def npv(r):
        arr = np.array(days)
        vals = np.array(amounts)
        return np.sum(vals / (1 + r)**(arr / 365.0))
        
    # Check signs
    pos = any(a > 0 for a in amounts)
    neg = any(a < 0 for a in amounts)
    if not (pos and neg):
        return None # Can't calculate IRR without both inflows and outflows
        
    try:
        res = optimize.newton(npv, 0.1, maxiter=50) # start guess at 10%
        return res
    except RuntimeError:
        return None
        
# Example usage block (not executed on import)
if __name__ == "__main__":
    pass
