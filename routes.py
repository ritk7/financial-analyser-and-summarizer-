from flask import render_template, redirect, url_for, request, flash, session, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import matplotlib
matplotlib.use('Agg')

from models import User, Transaction
from parser import StatementParser
from categorizer import TransactionCategorizer
from analyzer import FinancialAnalyzer
from report import ReportGenerator
from config import Config

def init_routes(app):
    # Get the login_manager from the app
    login_manager = app.login_manager
    
    # Register the user loader callback with LoginManager
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))
    
    # Ensure the upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # @app.route('/')
    # def index():
    #     if current_user.is_authenticated:
    #         return redirect(url_for('dashboard'))
    #     return redirect(url_for('login'))

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        return render_template('aboutus.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username') 
            password = request.form.get('password')
            
            user = User.get_by_username(username)
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            
            flash('Invalid username/email or password')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.get_by_username(username):
                flash('Username already exists')
                return render_template('register.html')
            
            user = User.create_user(name, username, email, password)
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
    
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if request.method == 'POST':
            # Check if file part exists
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            
            file = request.files['file']
            bank = request.form.get('bank')
            
            # Check if user selected a file
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            # Check if bank is selected
            if not bank:
                flash('Please select a bank')
                return redirect(request.url)
            
            # Check if file type is allowed
            if not (file.filename.endswith('.pdf') or file.filename.endswith('.csv')):
                flash('Only PDF and CSV files are allowed')
                return redirect(request.url)
            
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            try:
                # Debug message
                print(f"Processing file: {file_path}")
                print(f"Selected bank: {bank}")
                
                # Parse the statement
                parser = StatementParser()
                transactions = parser.parse(file_path, bank, current_user.id)
                
                # Debug message
                print(f"Parsed {len(transactions)} transactions")
                
                # Categorize transactions
                categorizer = TransactionCategorizer()
                categorized_transactions = categorizer.bulk_categorize(transactions)
                
                # Debug message
                print(f"Categorized {len(categorized_transactions)} transactions")
                
                # Save transactions to the database
                Transaction.save_transactions(categorized_transactions, current_user.id)
                
                flash(f"Successfully processed {len(transactions)} transactions")
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error processing file: {str(e)}")
                print(f"Error details: {error_details}")
                flash(f"Error processing file: {str(e)}")
                return redirect(request.url)
            finally:
                # Clean up the uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        return render_template('upload.html')
        return render_template('upload.html')
    
    @app.route('/api/stats')
    @login_required
    def get_stats():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        stats = analyzer.get_basic_stats()
        
        return jsonify(stats)
    
    @app.route('/api/categories')
    @login_required
    def get_categories():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        categories = analyzer.get_category_breakdown()
        
        return jsonify(categories)
    
    @app.route('/api/monthly')
    @login_required
    def get_monthly():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        monthly = analyzer.get_monthly_breakdown()
        
        return jsonify(monthly)
    
    @app.route('/api/heatmap')
    @login_required
    def get_heatmap():
        try:
            # Get all transactions for the current user
            transactions = Transaction.get_user_transactions(current_user.id)
            
            # Log the number of transactions
            print(f"Retrieved {len(transactions)} transactions for heatmap")
            
            # Analyze transactions
            analyzer = FinancialAnalyzer(transactions)
            heatmap = analyzer.get_daily_heatmap()
            
            # Log the heatmap data
            print(f"Generated heatmap with {len(heatmap)} data points")
            
            return jsonify(heatmap)
        except Exception as e:
            print(f"Error in heatmap endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/anomalies')
    @login_required
    def get_anomalies():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        anomalies = analyzer.detect_anomalies()
        
        return jsonify(anomalies)
    
    @app.route('/api/projections')
    @login_required
    def get_projections():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        projections = analyzer.project_monthly_spending()
        
        return jsonify(projections)
    
    @app.route('/api/recurring')
    @login_required
    def get_recurring():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        recurring = analyzer.identify_recurring_transactions()
        
        # Convert to JSON-serializable format
        recurring_data = []
        if recurring:  # Add check to ensure recurring is not None
            for transaction in recurring:
                if transaction.is_recurring:
                    recurring_data.append({
                        'id': transaction.id,
                        'date': transaction.date,
                        'description': transaction.description,
                        'amount': transaction.amount,
                        'category': transaction.category
                    })
        
        return jsonify(recurring_data)
    
    @app.route('/api/update_category', methods=['POST'])
    @login_required
    def update_category():
        data = request.json
        transaction_id = data.get('transaction_id')
        new_category = data.get('category')
        
        if not transaction_id or not new_category:
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        try:
            Transaction.update_transaction_category(transaction_id, new_category)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/report')
    @login_required
    def generate_report():
        # Get all transactions for the current user
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        analyzer = FinancialAnalyzer(transactions)
        
        # Generate report
        report_gen = ReportGenerator(analyzer, current_user.username)
        report_path = os.path.join(Config.UPLOAD_FOLDER, f"financial_report_{current_user.id}.pdf")
        
        report_gen.generate_pdf(report_path)
        
        return send_file(report_path, as_attachment=True, download_name="Financial_Report.pdf")