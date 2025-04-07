import csv
import pandas as pd
import pdfplumber
import re
import datetime
from io import StringIO
from models import Transaction

class StatementParser:
    def __init__(self):
        self.parsers = {
            'sbi': self.parse_sbi,
            'hdfc': self.parse_hdfc,
            'axis': self.parse_axis
        }
    
    def parse(self, file_path, bank_name, user_id):
        """Parse bank statement file and return transactions"""
        bank_name = bank_name.lower()
        if bank_name not in self.parsers:
            raise ValueError(f"Unsupported bank: {bank_name}. Supported banks: {', '.join(self.parsers.keys())}")
        
        if file_path.endswith('.pdf'):
            return self._parse_pdf(file_path, bank_name, user_id)
        elif file_path.endswith('.csv'):
            return self._parse_csv(file_path, bank_name, user_id)
        else:
            raise ValueError("Unsupported file format. Only PDF and CSV are supported.")
    
    def _parse_pdf(self, file_path, bank_name, user_id):
        """Extract text from PDF and parse it using the appropriate bank parser"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Use the appropriate parser based on bank name
        return self.parsers[bank_name](text, user_id, is_pdf=True)
    
    def _parse_csv(self, file_path, bank_name, user_id):
        """Parse CSV file using the appropriate bank parser"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Use the appropriate parser based on bank name
        return self.parsers[bank_name](content, user_id, is_pdf=False)
    
    def parse_sbi(self, content, user_id, is_pdf=False):
        """
        Parse SBI bank statement and return normalized transactions
        SBI Format Example (CSV):
        Date,Description,Debit,Credit,Balance
        01/04/2023,SALARY,0.00,50000.00,50000.00
        05/04/2023,ELECTRICITY BILL,2500.00,0.00,47500.00
        """
        transactions = []
        
        if is_pdf:
            # For PDF, extract data using regex
            pattern = r'(\d{2}/\d{2}/\d{4})\s+(.*?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})'
            matches = re.findall(pattern, content)
            
            for match in matches:
                date_str, description, debit, credit, balance = match
                date = datetime.datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                
                if float(debit) > 0:
                    amount = float(debit)
                    transaction_type = 'debit'
                else:
                    amount = float(credit)
                    transaction_type = 'credit'
                
                transactions.append(Transaction(
                    user_id=user_id,
                    date=date,
                    description=description.strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    bank='sbi'
                ))
        else:
            # For CSV, use pandas to parse
            df = pd.read_csv(StringIO(content))
            
            for _, row in df.iterrows():
                date = datetime.datetime.strptime(row['Date'], '%d/%m/%Y').strftime('%Y-%m-%d')
                
                # Determine if it's a debit or credit transaction
                debit = float(row['Debit']) if pd.notna(row['Debit']) and row['Debit'] != '' else 0.0
                credit = float(row['Credit']) if pd.notna(row['Credit']) and row['Credit'] != '' else 0.0
                
                if debit > 0:
                    amount = debit
                    transaction_type = 'debit'
                else:
                    amount = credit
                    transaction_type = 'credit'
                
                transactions.append(Transaction(
                    user_id=user_id,
                    date=date,
                    description=row['Description'].strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    bank='sbi'
                ))
        
        return transactions
    
    def parse_hdfc(self, content, user_id, is_pdf=False):
        """
        Parse HDFC bank statement and return normalized transactions
        HDFC Format Example (CSV):
        Date,Narration,Withdrawal Amt.,Deposit Amt.,Closing Balance
        01/04/2023,SALARY,,50000.00,50000.00
        05/04/2023,ELECTRICITY BILL,2500.00,,47500.00
        """
        transactions = []
        
        if is_pdf:
            # For PDF, extract data using regex
            pattern = r'(\d{2}/\d{2}/\d{4})\s+(.*?)\s+(\d+\.\d{2})?\s+(\d+\.\d{2})?\s+(\d+\.\d{2})'
            matches = re.findall(pattern, content)
            
            for match in matches:
                date_str, description = match[0], match[1]
                withdrawal = match[2] if match[2] else "0.00"
                deposit = match[3] if match[3] else "0.00"
                
                date = datetime.datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                
                if float(withdrawal) > 0:
                    amount = float(withdrawal)
                    transaction_type = 'debit'
                else:
                    amount = float(deposit)
                    transaction_type = 'credit'
                
                transactions.append(Transaction(
                    user_id=user_id,
                    date=date,
                    description=description.strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    bank='hdfc'
                ))
        else:
            # For CSV, use pandas to parse
            df = pd.read_csv(StringIO(content))
            
            # Rename columns to handle different possible column names
            if 'Withdrawal Amt.' in df.columns:
                df = df.rename(columns={'Withdrawal Amt.': 'Withdrawal'})
            if 'Deposit Amt.' in df.columns:
                df = df.rename(columns={'Deposit Amt.': 'Deposit'})
            if 'Narration' in df.columns:
                df = df.rename(columns={'Narration': 'Description'})
            
            for _, row in df.iterrows():
                date = datetime.datetime.strptime(row['Date'], '%d/%m/%Y').strftime('%Y-%m-%d')
                
                # Determine if it's a debit or credit transaction
                withdrawal = float(row['Withdrawal']) if pd.notna(row['Withdrawal']) and row['Withdrawal'] != '' else 0.0
                deposit = float(row['Deposit']) if pd.notna(row['Deposit']) and row['Deposit'] != '' else 0.0
                
                if withdrawal > 0:
                    amount = withdrawal
                    transaction_type = 'debit'
                else:
                    amount = deposit
                    transaction_type = 'credit'
                
                transactions.append(Transaction(
                    user_id=user_id,
                    date=date,
                    description=row['Description'].strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    bank='hdfc'
                ))
        
        return transactions
    
    def parse_axis(self, content, user_id, is_pdf=False):
        """
        Parse Axis bank statement and return normalized transactions
        Axis Format Example (CSV):
        Tran Date,Particulars,Dr Amount,Cr Amount,Balance
        01-04-2023,SALARY,,50000.00,50000.00
        05-04-2023,BILL PAYMENT,2500.00,,47500.00
        """
        transactions = []
        
        if is_pdf:
            # For PDF, extract data using regex
            pattern = r'(\d{2}-\d{2}-\d{4})\s+(.*?)\s+(\d+\.\d{2})?\s+(\d+\.\d{2})?\s+(\d+\.\d{2})'
            matches = re.findall(pattern, content)
            
            for match in matches:
                date_str, description = match[0], match[1]
                debit = match[2] if match[2] else "0.00"
                credit = match[3] if match[3] else "0.00"
                
                date = datetime.datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
                
                if float(debit) > 0:
                    amount = float(debit)
                    transaction_type = 'debit'
                else:
                    amount = float(credit)
                    transaction_type = 'credit'
                
                transactions.append(Transaction(
                    user_id=user_id,
                    date=date,
                    description=description.strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    bank='axis'
                ))
        else:
            # For CSV, use pandas to parse
            df = pd.read_csv(StringIO(content))
            
            if 'Tran Date' in df.columns:
                df = df.rename(columns={'Tran Date': 'Date'})
            if 'Dr Amount' in df.columns:
                df = df.rename(columns={'Dr Amount': 'Debit'})
            if 'Cr Amount' in df.columns:
                df = df.rename(columns={'Cr Amount': 'Credit'})
            if 'Particulars' in df.columns:
                df = df.rename(columns={'Particulars': 'Description'})
            
            for _, row in df.iterrows():
                # Handle different date formats
                try:
                    date = datetime.datetime.strptime(row['Date'], '%d-%m-%Y').strftime('%Y-%m-%d')
                except ValueError:
                    date = datetime.datetime.strptime(row['Date'], '%d/%m/%Y').strftime('%Y-%m-%d')
                
                debit = float(row['Debit']) if pd.notna(row['Debit']) and row['Debit'] != '' else 0.0
                credit = float(row['Credit']) if pd.notna(row['Credit']) and row['Credit'] != '' else 0.0
                
                if debit > 0:
                    amount = debit
                    transaction_type = 'debit'
                else:
                    amount = credit
                    transaction_type = 'credit'
                
                transactions.append(Transaction(
                    user_id=user_id,
                    date=date,
                    description=row['Description'].strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    bank='axis'
                ))
        
        return transactions