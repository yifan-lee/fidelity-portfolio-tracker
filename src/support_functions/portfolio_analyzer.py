from inspect import BoundArguments
import pandas as pd
from support_functions.data_loader import load_data
from support_functions.flow_builders import (
    EntityCashFlows,
    build_entity_cash_flows, 
    build_asset_class_cash_flows,
    build_account_cash_flows
)
from support_functions.math_utils import calculate_metrics

class PortfolioAnalyzer:
    def __init__(self, data_dir, output_dir=None):
        self.data = load_data(data_dir)
        self.output_dir = output_dir

    def analyze_entity_in_account(
        self, 
        account_num: str, 
        entity_name: str
    ):
        entity_cash_flows = build_entity_cash_flows(self.data, account_num, entity_name)
        metrics = calculate_metrics(entity_cash_flows)
        account_name = self.data.account_map.get(account_num, "Unknown")

        result = pd.Series({
            'Account Number': account_num,
            'Account Name': account_name,
            'Entity Name': entity_name,
            'Total Invested': entity_cash_flows.total_invested,
            'Current Basis': entity_cash_flows.current_basis,
            'Current Value': entity_cash_flows.current_value,
            'Total PnL': metrics['Total PnL'],
            'IRR (%)': f"{metrics['IRR']:.2%}" if metrics['IRR'] is not None else "N/A",
            'Total Return (%)': f"{metrics['ROI']:.2%}",
            'Holding Period (Y)': f"{metrics['Holding Period (Y)']:.2f}"
        })
        return result

    def analyze_all_entities_in_account(
        self,
        account_num: str
    ):
        results = []
        sub_transactions = self.data.transactions[self.data.transactions['Account Number'] == account_num]
        entity_name_list = sub_transactions['Symbol'].unique()
        entity_name_list = entity_name_list[entity_name_list != '']
        for entity_name in entity_name_list:
            result = self.analyze_entity_in_account(account_num, entity_name)
            results.append(result)
        results = pd.DataFrame(results)
        if not results.empty and 'Current Value' in results.columns:
            ratio = results['Current Value'] / results['Current Value'].sum()
            results['Investment Ratio'] = ratio.apply(lambda x: f"{x:.2%}")
            return results.sort_values('Current Value', ascending=False)
        return results


    def analyze_account_by_asset_class(
        self,
        account_num: str
    ):
        results = []
        account_name = self.data.account_map.get(account_num, "Unknown")
        funding_cash_flows = build_asset_class_cash_flows(self.data, account_num, 'Transfer')
        total_funding = sum(amount for date, amount in funding_cash_flows.cash_flows)
        
        for asset_class in ["Stock", "Bond"]:
            asset_class_cash_flows = build_asset_class_cash_flows(self.data, account_num, asset_class)
            metrics = calculate_metrics(asset_class_cash_flows)
            results.append(pd.Series({
                'Account Number': account_num,
                'Account Name': account_name,
                'Asset Class': asset_class,
                'Total Invested': asset_class_cash_flows.total_invested,
                'Current Basis': asset_class_cash_flows.current_basis,
                'Current Value': asset_class_cash_flows.current_value,
                'Total PnL': metrics['Total PnL'],
                'IRR (%)': f"{metrics['IRR']:.2%}" if metrics['IRR'] is not None else "N/A",
                'Total Return (%)': f"{metrics['ROI']:.2%}",
                'Holding Period (Y)': f"{metrics['Holding Period (Y)']:.2f}"
            }))
            total_funding = total_funding - asset_class_cash_flows.current_basis
        
        cash_cash_flows = build_asset_class_cash_flows(self.data, account_num, 'Cash')
        results.append(pd.Series({
            'Account Number': account_num,
            'Account Name': account_name,
            'Asset Class': "Cash",
            'Total Invested': cash_cash_flows.total_invested,
            'Current Basis': total_funding,
            'Current Value': cash_cash_flows.current_value,
            'Total PnL': None,
            'IRR (%)': None,
            'Total Return (%)': None,
            'Holding Period (Y)': None
        }))
        results = pd.DataFrame(results)
        if not results.empty and 'Current Value' in results.columns:
            ratio = results['Current Value'] / results['Current Value'].sum()
            results['Investment Ratio'] = ratio.apply(lambda x: f"{x:.2%}")
            return results.sort_values('Current Value', ascending=False)
        return results
        


    def analyze_account_performance(self):
        unique_accounts = self.data.unique_accounts
        results = []
        
        for _, row in unique_accounts.iterrows():
            account_name = row['Account Name']
            account_num = row['Account Number']
            account_cash_flows = build_account_cash_flows(self.data, account_num)
            metrics = calculate_metrics(account_cash_flows)

            results.append({
                'Account Name': account_name,
                'Account Number': account_num,
                'Total Invested': account_cash_flows.total_invested,
                'Current Basis': account_cash_flows.current_basis,
                'Current Value': account_cash_flows.current_value,
                'Total PnL': metrics['Total PnL'],
                'IRR': f"{metrics['IRR']:.2%}" if metrics['IRR'] is not None else "N/A",
                'Total Return (%)': f"{metrics['ROI']:.2%}",
                'Holding Period (Y)': f"{metrics['Holding Period (Y)']:.2f}"
            })

        results = pd.DataFrame(results)
        if not results.empty and 'Total Invested' in results.columns:
            ratio = results['Total Invested'] / results['Total Invested'].sum()
            results['Investment Ratio'] = ratio.apply(lambda x: f"{x:.2%}")
            return results.sort_values('Total Invested', ascending=False)
        return results






    def analyze_portfolio_total(self):
        latest_date = self.data.latest_date
        unique_accounts = self.data.unique_accounts
        total_cash_flows = EntityCashFlows(latest_date=latest_date)

        for _, row in unique_accounts.iterrows():
            account_num = row['Account Number']
            entity_cash_flows = build_account_cash_flows(self.data, account_num)
            total_cash_flows.cash_flows.extend(entity_cash_flows.cash_flows)
            total_cash_flows.total_invested += entity_cash_flows.total_invested
            total_cash_flows.current_value += entity_cash_flows.current_value

        metrics = calculate_metrics(total_cash_flows)
        
        result = [{
            'Level': 'Portfolio',
            'Name': 'Total',
            'Current Value': total_cash_flows.current_value,
            'Total Invested': total_cash_flows.total_invested,
            'Total PnL': metrics['Total PnL'],
            'Total Return (%)': f"{metrics['ROI']:.2%}",
            'IRR': f"{metrics['IRR']:.2%}" if metrics['IRR'] is not None else "N/A",
            'Holding Period (Y)': f"{metrics['Holding Period (Y)']:.2f}"
        }]
        return pd.DataFrame(result)

    

    # def analyze_individual_account_performance(self):
    #     """3. Analyze performance aggregated by Asset Type (Stock, Bond, Cash) across non-excluded accounts."""
    #     results = []
    #     positions = self.data.positions

    #     # Filter relevant positions
    #     target_account = "Z23390746"
        
    #     relevant_positions = positions[positions['Account Number'] == target_account]
    #     asset_types = relevant_positions['Asset Type'].unique()

    #     for asset_type in asset_types:
    #         # if asset_type == 'Cash':
    #         #     # For Cash/Money Market, Transaction history is often messy (sweeps).
    #         #     # We use 'Cost Basis Total' from positions as a proxy for "Total Invested".
    #         #     # If Cost Basis is missing/0, we assume it equals Current Value (recent deposit).
    #         #     sub_positions = relevant_positions[relevant_positions['Asset Type'] == 'Cash']
                
    #         #     # Sum up values for all Cash positions
    #         #     curr_val_sum = sub_positions['Current Value'].sum()
    #         #     cost_basis_sum = sub_positions['Cost Basis Total'].sum()
                
    #         #     # Fallback if cost_basis is 0 but we have value (e.g. core position might show 0 basis intra-day?)
    #         #     # Usually for money market funds, basis is $1.00/share.
    #         #     if cost_basis_sum == 0 and curr_val_sum > 0:
    #         #         total_invested = curr_val_sum
    #         #     else:
    #         #         total_invested = cost_basis_sum
                    
    #         #     total_return_dollar = curr_val_sum - total_invested
    #         #     # Avoid div by zero
    #         #     roi = total_return_dollar / total_invested if total_invested > 0 else 0
                
    #         #     results.append({
    #         #         'Asset Type': asset_type,
    #         #         'Current Value': curr_val_sum,
    #         #         'Total Invested': total_invested,
    #         #         'Total Return ($)': total_return_dollar,
    #         #         'Total Return (%)': f"{roi:.2%}",
    #         #         'IRR': "N/A", # Hard to calc IRR for sweeps without perfect history
    #         #         'Holding Period (Y)': "N/A"
    #         #     })
    #         #     continue
            
    #         type_cash_flows = EntityCashFlows(latest_date=self.data.latest_date)
            
    #         # Find all symbols for this asset type in our target accounts
    #         # Note: A symbol might exist in different accounts, treating them as separate cash flow streams is safest.
    #         sub_positions = relevant_positions[relevant_positions['Asset Type'] == asset_type]
            
    #         for _, row in sub_positions.iterrows():
    #             symbol = row['Symbol']
    #             account_num = row['Account Number']
    #             if symbol == 'Pending activity': continue

    #             entity_flows = build_stock_cash_flows(self.data, account_num=account_num, symbol=symbol)
    #             type_cash_flows.cash_flows.extend(entity_flows.cash_flows)
    #             type_cash_flows.total_invested += entity_flows.total_invested
    #             type_cash_flows.current_value += entity_flows.current_value

    #         metrics = calculate_metrics(type_cash_flows)
            
    #         results.append({
    #             'Asset Type': asset_type,
    #             'Current Value': type_cash_flows.current_value,
    #             'Total Invested': type_cash_flows.total_invested,
    #             'Total Return ($)': metrics['Total Return ($)'],
    #             'Total Return (%)': f"{metrics['ROI']:.2%}",
    #             'IRR': f"{metrics['IRR']:.2%}" if metrics['IRR'] is not None else "N/A",
    #             'Holding Period (Y)': f"{metrics['Holding Period (Y)']:.2f}"
    #         })

    #     results = pd.DataFrame(results)
    #     if not results.empty and 'Total Invested' in results.columns:
    #         ratio = results['Total Invested'] / results['Total Invested'].sum()
    #         results['Investment Ratio'] = ratio.apply(lambda x: f"{x:.2%}")
    #         return results.sort_values('Total Invested', ascending=False)
    #     return results

    # def analyze_individual_account_holdings(self):
    #     """4. Analyze performance for every individual holding."""
    #     results = []
    #     positions = self.data.positions
    #     unique_accounts = self.data.unique_accounts

    #     for _, row in unique_accounts.iterrows():
    #         account_name = row['Account Name']
    #         account_num = row['Account Number']

    #         if account_name in self.excluded_accounts:
    #             continue
            
    #         # Get all positions for this account (Stock, Bond, etc.)
    #         sub_positions = positions[positions['Account Name'] == account_name]

    #         for _, sub_row in sub_positions.iterrows():
    #             symbol = sub_row['Symbol']
    #             asset_type = sub_row['Asset Type']
    #             if symbol in ['Pending activity']:
    #                 continue
            
    #             entity_cash_flows = build_stock_cash_flows(self.data, account_num=account_num, symbol=symbol)
    #             metrics = calculate_metrics(entity_cash_flows)
                    
    #             results.append({
    #                 'Account Name': account_name,
    #                 'Symbol': symbol,
    #                 'Asset Type': asset_type,
    #                 'Current Value': entity_cash_flows.current_value,
    #                 'Total Invested': entity_cash_flows.total_invested,
    #                 'Total Return ($)': metrics['Total Return ($)'],
    #                 'Total Return (%)': f"{metrics['ROI']:.2%}",
    #                 'IRR': f"{metrics['IRR']:.2%}" if metrics['IRR'] is not None else "N/A",
    #                 'Holding Period (Y)': f"{metrics['Holding Period (Y)']:.2f}"
    #             })
        
    #     results = pd.DataFrame(results)
    #     if not results.empty and 'Total Invested' in results.columns:
    #         # Sort by total invested
    #         return results.sort_values('Total Invested', ascending=False)
    #     return results




