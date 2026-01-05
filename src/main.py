from support_functions.data_loader import (
    load_data
)
from support_functions.analysis import (
    analyze_account_performance,
    analyze_stock_performance,
    analyze_total_performance
)

from pathlib import Path


def main():
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    positions_df, transactions_df, latest_date = load_data(data_dir)
    
    print("\n" + "="*50)
    print("FIDELITY PORTFOLIO ANALYSIS")
    print("="*50)
    
    # 1. Total Portfolio Performance
    print("\nCalculating total portfolio performance...")
    results = analyze_total_performance(positions_df, transactions_df, latest_date)
    print(results)
    
    # 2. Calculate performance for all positions
    print("\nCalculating performance for each account...")
    results = analyze_account_performance(positions_df, transactions_df, latest_date)
    print(results)
    
    # 3. Each Account -> Each Stock
    print("\nCalculating performance for Account & Symbol...")
    results = analyze_stock_performance(positions_df, transactions_df, latest_date)
    print(results)
    

if __name__ == "__main__":
    main()
