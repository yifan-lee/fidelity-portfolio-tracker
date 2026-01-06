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
    report.append(total_df.to_markdown(index=False, floatfmt=".2f"))
    report.append("\n")
    
    # 2. Account Level Performance
    report.append("## 2. Performance by Account")
    report.append(account_df.to_markdown(index=False, floatfmt=".2f"))
    report.append("\n")
    
    # 3. Position Details
    report.append("## 3. Performance by Stocks")
    report.append(stock_df.to_markdown(index=False, floatfmt=".2f"))
    report.append("\n")

    report_content = "\n".join(report)
    
    if output_dir:
        filename = f"Portfolio_Report_{report_date.strftime('%Y-%m-%d')}.md"
        output_path = f"{output_dir}/{filename}"
        with open(output_path, "w") as f:
            f.write(report_content)
        print(f"Report saved to: {output_path}")
        
    return report_content
