class Portfolio:
    def __init__(self, transactions, position):
        self.transactions = transactions
        self.position = position
        
        self.individual_transactions = self.transactions[self.transactions['Account']=='Individual Z23390746']
        self.individual_position = self.position[self.position['Account Number']=='Z23390746']