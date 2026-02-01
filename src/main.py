
from support_functions.portfolio_analyzer import PortfolioAnalyzer
from support_functions.report_generator import generate_markdown_report

from pathlib import Path


def main():
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    output_dir = f'{project_path}/output'
    
    # Initialize Analyzer
    analyzer = PortfolioAnalyzer(data_dir, output_dir)
    
    print("\n" + "="*50)
    print("FIDELITY PORTFOLIO ANALYSIS")
    print("="*50)
    
    # 1. Total Portfolio Performance
    print("Calculating metrics...")
    total_res = analyzer.analyze_portfolio_total()
    
    # 2. Account Performance
    account_res = analyzer.analyze_account_performance()
    
    # 3. Asset Type Performance
    asset_type_res = analyzer.analyze_account_by_asset_class('Z23390746')

    # 4. Individual Holdings
    holdings_res = analyzer.analyze_all_entities_in_account('Z23390746')

    # Generate Report
    output_dir = project_path / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # We need to update report generator to accept asset_type_res
    # For now, let's just print to console to verify, and pass placeholders to report if needed
    # Or overloading the arguments if possible.
    # The user didn't ask to rewrite report_generator yet, but we should make sure it doesn't break.
    # Previous report_generator signature: (total_res, account_res, stock_res, latest_date, output_dir)
    # We will pass holdings_res as third arg. asset_type_res will be printed for now.
    
    report_str = generate_markdown_report(total_res, account_res, holdings_res, analyzer.data.latest_date, output_dir=str(output_dir))
    
    print("\n" + "="*50)
    print("ASSET TYPE SUMMARY")
    print(asset_type_res)
    print("="*50)
    print(report_str)
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
