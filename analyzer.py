import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from models import Transaction

class FinancialAnalyzer:
    def __init__(self, transactions):
        """Initialize with a list of Transaction objects"""
        self.transactions = transactions
        self.df = self._create_dataframe()
    
    def _create_dataframe(self):
        """Convert transactions to a pandas DataFrame for analysis"""
        data = []
        
        for transaction in self.transactions:
            data.append({
                'id': transaction.id,
                'date': transaction.date,
                'description': transaction.description,
                'amount': transaction.amount,
                'type': transaction.transaction_type,
                'category': transaction.category,
                'is_recurring': transaction.is_recurring,
                'bank': transaction.bank
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.strftime('%Y-%m')
            df['week'] = df['date'].dt.strftime('%Y-%W')
            df['day'] = df['date'].dt.day
            
            df['debit'] = df.apply(lambda row: row['amount'] if row['type'] == 'debit' else 0, axis=1)
            df['credit'] = df.apply(lambda row: row['amount'] if row['type'] == 'credit' else 0, axis=1)
        
        return df
    
    def get_basic_stats(self):
        """Get basic statistics about transactions"""
        if self.df.empty:
            return {
                'total_transactions': 0,
                'total_debit': 0,
                'total_credit': 0,
                'net_cashflow': 0,
                'average_transaction': 0
            }
        
        return {
            'total_transactions': len(self.df),
            'total_debit': round(self.df['debit'].sum(), 2),
            'total_credit': round(self.df['credit'].sum(), 2),
            'net_cashflow': round(self.df['credit'].sum() - self.df['debit'].sum(), 2),
            'average_transaction': round(self.df['amount'].mean(), 2)
        }
    
    def get_category_breakdown(self):
        """Get spending breakdown by category"""
        if self.df.empty:
            return []
        
        debits_df = self.df[self.df['type'] == 'debit']
        
        if debits_df.empty:
            return []
        
        category_totals = debits_df.groupby('category')['amount'].sum().reset_index()
        category_totals = category_totals.sort_values('amount', ascending=False)
        
        result = []
        for _, row in category_totals.iterrows():
            result.append({
                'category': row['category'],
                'amount': round(row['amount'], 2)
            })
        
        return result
    
    def get_monthly_breakdown(self):
        """Get monthly spending breakdown"""
        if self.df.empty:
            return []
        
        monthly_data = []
        
        monthly_category = self.df.groupby(['month', 'category']).agg({
            'debit': 'sum',
            'credit': 'sum'
        }).reset_index()
        
        months = sorted(monthly_category['month'].unique())
        categories = sorted(monthly_category['category'].unique())
        
        for month in months:
            month_data = {
                'month': month,
                'total_debit': round(
                    monthly_category[monthly_category['month'] == month]['debit'].sum(), 2
                ),
                'total_credit': round(
                    monthly_category[monthly_category['month'] == month]['credit'].sum(), 2
                ),
                'categories': {}
            }
            
            for category in categories:
                filtered = monthly_category[
                    (monthly_category['month'] == month) & 
                    (monthly_category['category'] == category)
                ]
                
                if not filtered.empty:
                    month_data['categories'][category] = {
                        'debit': round(filtered['debit'].sum(), 2),
                        'credit': round(filtered['credit'].sum(), 2)
                    }
            
            monthly_data.append(month_data)
        
        return monthly_data
    
    def get_daily_heatmap(self):
        """Get daily spending data for heatmap"""
        if self.df.empty:
            return []
        
        daily_spent = self.df[self.df['type'] == 'debit'].groupby(self.df['date'].dt.date)['amount'].sum()
        
        result = []
        for date, amount in daily_spent.items():
            result.append({
                'date': date.strftime('%Y-%m-%d'),
                'amount': round(amount, 2)
            })
        
        return result
    
    def identify_recurring_transactions(self, min_occurrences=2, time_window_days=45):
        """Identify recurring transactions based on description and amount"""
        if self.df.empty:
            return []
        
        grouped = self.df.groupby(['description', 'amount'])
        
        recurring_ids = []
        
        for (desc, amount), group in grouped:
            if len(group) >= min_occurrences:
                sorted_group = group.sort_values('date')
                
                dates = sorted_group['date'].tolist()
                is_recurring = False
                
                for i in range(len(dates) - 1):
                    days_diff = (dates[i+1] - dates[i]).days
                    
                    if days_diff <= time_window_days:
                        is_recurring = True
                        break
                
                if is_recurring:
                    recurring_ids.extend(sorted_group['id'].tolist())
        
        self.df.loc[self.df['id'].isin(recurring_ids), 'is_recurring'] = True
        
        for transaction in self.transactions:
            if transaction.id in recurring_ids:
                transaction.is_recurring = True
        
        return self.transactions
    
    def detect_anomalies(self, z_threshold=2.0):
        """Detect anomalies using Z-score method"""
        if self.df.empty:
            return []
        
        anomalies = []
        
        for category in self.df['category'].unique():
            category_df = self.df[self.df['category'] == category]
            
            if len(category_df) <= 1:
                continue
            
            mean = category_df['amount'].mean()
            std = category_df['amount'].std()
            
            if std == 0:
                continue
            
            for _, row in category_df.iterrows():
                z_score = (row['amount'] - mean) / std
                
                if abs(z_score) > z_threshold:
                    anomalies.append({
                        'id': row['id'],
                        'date': row['date'].strftime('%Y-%m-%d'),
                        'description': row['description'],
                        'amount': round(row['amount'], 2),
                        'category': category,
                        'z_score': round(z_score, 2)
                    })
        
        return anomalies
    
    def project_monthly_spending(self):
        """Project spending for the current month based on past trends"""
        if self.df.empty:
            return {}
        
        today = datetime.now()
        
        days_in_month = (datetime(today.year, today.month + 1 if today.month < 12 else 1, 1) - 
                        datetime(today.year, today.month, 1)).days
        days_elapsed = today.day
        days_remaining = days_in_month - days_elapsed
        
        current_month = today.strftime('%Y-%m')
        curr_month_df = self.df[(self.df['month'] == current_month) & (self.df['type'] == 'debit')]
        
        if curr_month_df.empty:
            return {}
        
        projections = {}
        
        category_spent = curr_month_df.groupby('category')['amount'].sum()
        
        for category, amount in category_spent.items():
            daily_avg = amount / days_elapsed
            projected_amount = amount + (daily_avg * days_remaining)
            
            prev_month = (today - timedelta(days=30)).strftime('%Y-%m')
            prev_month_spent = 0
            
            prev_df = self.df[
                (self.df['month'] == prev_month) & 
                (self.df['category'] == category) & 
                (self.df['type'] == 'debit')
            ]
            
            if not prev_df.empty:
                prev_month_spent = prev_df['amount'].sum()
            
            is_overshoot = projected_amount > (prev_month_spent * 1.2) if prev_month_spent > 0 else False
            
            projections[category] = {
                'current_spent': round(amount, 2),
                'projected_amount': round(projected_amount, 2),
                'previous_month': round(prev_month_spent, 2),
                'possible_overshoot': int(is_overshoot) 
            }
        
        total_spent = category_spent.sum()
        total_projected = total_spent / days_elapsed * days_in_month
        
        prev_month = (today - timedelta(days=30)).strftime('%Y-%m')
        prev_month_total = self.df[
            (self.df['month'] == prev_month) & 
            (self.df['type'] == 'debit')
        ]['amount'].sum()
        
        total_overshoot = total_projected > (prev_month_total * 1.1) if prev_month_total > 0 else False
        
        projections['total'] = {
            'current_spent': round(total_spent, 2),
            'projected_amount': round(total_projected, 2),
            'previous_month': round(prev_month_total, 2),
            'possible_overshoot': int(total_overshoot)  # Convert boolean to integer (0 or 1)
        }
        
        return projections