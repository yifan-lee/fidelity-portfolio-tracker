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
    print("Calculating metrics...")
    total_res = analyze_total_performance(positions_df, transactions_df, latest_date)
    
    # 2. Calculate performance for all positions
    account_res = analyze_account_performance(positions_df, transactions_df, latest_date)
    
    # 3. Stock Level
    stock_res = analyze_stock_performance(positions_df, transactions_df, latest_date)

    # Generate Report
    from support_functions.report import generate_markdown_report
    report_str = generate_markdown_report(total_res, account_res, stock_res, latest_date)
    
    print("\n" + "="*50)
    print(report_str)
    print("="*50 + "\n")
    
    # Note: Requirement #4 Asset Class aggregation was removed in previous user edits?
    # If not, we should re-add it if needed. For now sticking to the 3 DFs user showed.
    

if __name__ == "__main__":
    main()
