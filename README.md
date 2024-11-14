# fidelity-portfolio-tracker

<!-- ![Project Logo](https://example.com/logo.png) -->

## Table of Contents


- [About](#about)
- [Usage](#usage)
- [Code](#code)
- [Data](#data)

## About

**fidelity-portfolio-tracker** is used to track the returns of my fidelity protfolio.

## Usage

Run the following code.

```bash
python ./code/main.py
```

It will display the distribution of investments and irr of each stock bought in individual account.

## Code

### portfolio.py

Provide Portfolio class with historical transactions and current position as inputs.

Currently, its main attributes are:
```python
# create portfolio object
current_portfolio = Portfolio(transactions=transactions, position=position)
# display the distribution of investments in individual account
current_portfolio.show_investment_distribution()
# display the irr of each stock bought in individual account
current_portfolio.show_stock_irr()
```

### data_loader.py

- load_position: load the latest downloaded position from **data** file.
- load_transaction: load all downloaded transactions from **data** file.

## Data

Transaction and position files downloaded from Fidelity.


