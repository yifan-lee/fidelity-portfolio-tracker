from datetime import datetime
import pandas as pd

def generate_markdown_report(total_df, account_df, stock_df, report_date, output_dir=None):
    """
    Generates a Markdown formatted report string from the analysis DataFrames.
    """
    
    report = []
    
    # Title and Date
    report.append(f"# Fidelity Portfolio Analysis Report")
    report.append(f"**Date:** {report_date.strftime('%Y-%m-%d')}\n")
    
    # 1. Total Portfolio Performance
    report.append("## 1. Total Portfolio Performance")
    # We can transpose the total df for a summary view if it's just one row,
    # or keep it as a table. A table is fine.
    # Hide empty columns if any (like Account Name/Number for Total row)
    clean_total = total_df.dropna(axis=1, how='all')
    report.append(clean_total.to_markdown(index=False, floatfmt=".2f"))
    report.append("\n")
    
    # 2. Account Level Performance
    report.append("## 2. Performance by Account")
    # Clean up the dataframe for display
    # Maybe drop 'Symbol' or 'Asset Type' if they are redundant for account view
    cols_to_show = [
        'Account Name', 'Account Number', 'Current Value', 
        'Total Invested', 'Total Return ($)', 'Total Return (%)', 
        'IRR', 'Investment Ratio'
    ]
    # Ensure cols exist
    existing_cols = [c for c in cols_to_show if c in account_df.columns]
    report.append(account_df[existing_cols].to_markdown(index=False, floatfmt=".2f"))
    report.append("\n")
    
    # 3. Position Details
    report.append("## 3. Performance by Stocks")
    # Group by Account for better readability?
    # Or just one big table. User previous output was grouped by Account in print loop.
    # A single sorted table is often better for a report, maybe sort by Investment Ratio or Account.
    # Let's keep the user's sort order (Total Invested desc).
    
    cols_to_show_stock = [
        'Account Name', 'Symbol', 'Current Value', 
        'Total Invested', 'Total Return ($)', 'Total Return (%)', 
        'IRR', 'Investment Ratio'
    ]
    existing_cols_stock = [c for c in cols_to_show_stock if c in stock_df.columns]
    
    report.append(stock_df[existing_cols_stock].to_markdown(index=False, floatfmt=".2f"))
    report.append("\n")
    
    report_content = "\n".join(report)
    
    if output_dir:
        filename = f"Portfolio_Report_{report_date.strftime('%Y-%m-%d')}.md"
        output_path = f"{output_dir}/{filename}"
        with open(output_path, "w") as f:
            f.write(report_content)
        print(f"Report saved to: {output_path}")
        
    return report_content
