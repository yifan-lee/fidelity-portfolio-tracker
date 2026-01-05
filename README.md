# Fidelity Portfolio Analyzer

A Python-based tool to analyze your Fidelity investment performance by processing exported portfolio and transaction data. It provides insights into total returns, account-level performance, and individual stock gains/losses.

## 🌟 Features

- Total Returns: Comprehensive analysis of overall gain/loss across all linked accounts.

- Account Performance: Breakdown of returns for each individual Fidelity account.

- Stock-Level Insights: Detailed performance tracking for every ticker/holding.

- Automated Reporting: Generates a clean, readable Markdown report in the output/ folder.

## 📂 Project Structure
- **data/**: Directory for input files (CSV exports from Fidelity).

- **output/**: Directory where the generated analysis reports are saved.

- **main.py**: The primary script to execute the analysis.

🚀 Getting Started

1. Data Preparation

    1. Log in to your Fidelity account.

    2. Export your Portfolio Positions and Transaction History as CSV files.

    3. Place these CSV files into the data/ folder.

2. Run the Analysis

    Ensure you have Python and necessary dependencies (like pandas) installed, then run: python main.py

3. View Results

    Open the output/ folder to find your generated Markdown report.

## 🔒 Privacy & Security

- Local Execution: All data processing is done locally on your machine. Your sensitive financial data never leaves your computer.

- Git Safety: The data/ and output/ folders are pre-configured in .gitignore to ensure your private financial information is never accidentally uploaded to GitHub.

-----------

# 富达投资组合分析工具 (Fidelity Portfolio Analyzer)

这是一个基于 Python 的工具，通过处理从 Fidelity (富达投资) 导出的投资组合位置和交易历史数据，自动分析您的投资表现。它可以为您提供总体收益、各账户表现以及每只股票的盈亏明细。

## 🌟 功能特点
- 总体收益分析：汇总分析所有账户的整体盈亏情况。

- 账户维度表现：按不同的富达账户拆解投资回报。

- 个股盈亏追踪：详细追踪每只股票/标的的具体表现。

- 自动生成报告：在 output/ 文件夹中自动生成整洁的 Markdown 格式分析报告。

## 📂 项目结构

- **data/**: 存放输入文件（从 Fidelity 导出的 CSV 文件）。

- **output/**: 存放生成的分析报告。

- **main.py**: 执行分析的主程序脚本。

## 🚀 快速开始
1. 数据准备
    1. 登录您的 Fidelity 账户。
    2. 将您的 Portfolio Positions (持仓) 和 Transaction History (交易历史) 导出为 CSV 文件。
    3. 将导出的 CSV 文件放入项目的 data/ 文件夹中。

2. 运行分析

    确保您的环境中已安装 Python 以及必要的库（如 pandas），然后在终端运行： python main.py

3. 查看报告

    运行完成后，前往 output/ 文件夹查看最新的 Markdown 报告。

## 🔒 隐私与安全

- 本地处理：所有数据均在您的本地机器上处理。您的敏感财务信息绝不会离开您的计算机。

- Git 忽略设置：data/ 和 output/ 文件夹已在 .gitignore 中配置，确保您的私密财务数据不会被意外上传到 GitHub 远程仓库。