
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
import os
import base64
from datetime import datetime

class ReportGenerator:
    def __init__(self, analyzer, user_name):
        self.analyzer = analyzer
        self.user_name = user_name
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        self.heading2_style = ParagraphStyle(
            'Heading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6
        )
        self.normal_style = self.styles['Normal']
    
    def generate_pdf(self, output_path):
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        elements = []
        
        title = Paragraph(f"Financial Analysis Report for {self.user_name}", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        report_date = Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.normal_style)
        elements.append(report_date)
        elements.append(Spacer(1, 24))
        
        elements.append(Paragraph("Financial Summary", self.heading2_style))
        stats = self.analyzer.get_basic_stats()
        stats_data = [
            ["Metric", "Value"],
            ["Total Transactions", str(stats['total_transactions'])],
            ["Total Debits", f"₹{stats['total_debit']:,.2f}"],
            ["Total Credits", f"₹{stats['total_credit']:,.2f}"],
            ["Net Cashflow", f"₹{stats['net_cashflow']:,.2f}"],
            ["Average Transaction", f"₹{stats['average_transaction']:,.2f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONT', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 24))
        
        elements.append(Paragraph("Spending by Category", self.heading2_style))
        categories = self.analyzer.get_category_breakdown()
        
        if categories:
            pie_img = self._create_category_pie_chart(categories)
            elements.append(pie_img)
            elements.append(Spacer(1, 12))
            
            cat_data = [["Category", "Amount"]]
            for cat in categories:
                cat_data.append([cat['category'].capitalize(), f"₹{cat['amount']:,.2f}"])
            
            cat_table = Table(cat_data, colWidths=[2.5*inch, 2.5*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('FONT', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                ('BACKGROUND', (0, 1), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ]))
            elements.append(cat_table)
            elements.append(Spacer(1, 24))
        else:
            elements.append(Paragraph("No category data available", self.normal_style))
            elements.append(Spacer(1, 24))
        
        # Monthly trends
        elements.append(Paragraph("Monthly Spending Trends", self.heading2_style))
        monthly_data = self.analyzer.get_monthly_breakdown()
        
        if monthly_data:
            # line chart of monthly spending
            monthly_img = self._create_monthly_chart(monthly_data)
            elements.append(monthly_img)
            elements.append(Spacer(1, 24))
        else:
            elements.append(Paragraph("No monthly data available", self.normal_style))
            elements.append(Spacer(1, 24))
        
        elements.append(Paragraph("Unusual Transactions", self.heading2_style))
        anomalies = self.analyzer.detect_anomalies()
        
        if anomalies:
            anomaly_data = [["Date", "Description", "Amount", "Category"]]
            for anomaly in anomalies:
                anomaly_data.append([
                    anomaly['date'],
                    anomaly['description'][:30] + "..." if len(anomaly['description']) > 30 else anomaly['description'],
                    f"₹{anomaly['amount']:,.2f}",
                    anomaly['category'].capitalize()
                ])
            
            anomaly_table = Table(anomaly_data, colWidths=[1*inch, 3*inch, 1*inch, 1.5*inch])
            anomaly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ]))
            elements.append(anomaly_table)
        else:
            elements.append(Paragraph("No unusual transactions detected", self.normal_style))
        
        elements.append(Spacer(1, 24))
        
        elements.append(Paragraph("Monthly Spending Projection", self.heading2_style))
        projections = self.analyzer.project_monthly_spending()
        
        if projections:
            category_projections = {k: v for k, v in projections.items() if k != 'total'}
            
            if category_projections:
                proj_data = [["Category", "Current", "Projected", "Previous Month", "Possible Overshoot"]]
                
                for category, data in category_projections.items():
                    proj_data.append([
                        category.capitalize(),
                        f"₹{data['current_spent']:,.2f}",
                        f"₹{data['projected_amount']:,.2f}",
                        f"₹{data['previous_month']:,.2f}",
                        "Yes" if data['possible_overshoot'] else "No"
                    ])
                
                total = projections.get('total', {})
                proj_data.append([
                    "TOTAL",
                    f"₹{total.get('current_spent', 0):,.2f}",
                    f"₹{total.get('projected_amount', 0):,.2f}",
                    f"₹{total.get('previous_month', 0):,.2f}",
                    "Yes" if total.get('possible_overshoot', False) else "No"
                ])
                
                proj_table = Table(proj_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                proj_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                elements.append(proj_table)
            else:
                elements.append(Paragraph("No projection data available", self.normal_style))
        else:
            elements.append(Paragraph("No projection data available", self.normal_style))
        
        doc.build(elements)
        return output_path
    
    def _create_category_pie_chart(self, categories):
        """Create a pie chart of spending by category"""
        plt.figure(figsize=(5, 5))
        
        labels = [cat['category'].capitalize() for cat in categories]
        sizes = [cat['amount'] for cat in categories]
        
        if len(labels) > 6:
            labels = labels[:5] + ["Other"]
            sizes = sizes[:5] + [sum(sizes[5:])]
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title('Spending by Category')
        
        # Save figure to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        
        buffer.seek(0)
        img = Image(buffer, width=4*inch, height=4*inch)
        return img
    
    def _create_monthly_chart(self, monthly_data):
        """Create a line chart of monthly spending trends"""
        plt.figure(figsize=(6, 4))
        
        months = [m['month'] for m in monthly_data]
        totals = [m['total_debit'] for m in monthly_data]
        
        plt.plot(months, totals, marker='o')
        plt.xlabel('Month')
        plt.ylabel('Total Spending')
        plt.title('Monthly Spending Trend')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        
        buffer.seek(0)
        img = Image(buffer, width=5*inch, height=3*inch)
        return img
