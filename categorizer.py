import re
import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class TransactionCategorizer:
    def __init__(self):
        self.categories = [
            'food', 'transportation', 'shopping', 'utilities', 
            'entertainment', 'health', 'education', 'travel', 
            'housing', 'income', 'investment', 'bills', 'other'
        ]
        #rule based
        self.rules = {
            'food': [
                r'swiggy', r'zomato', r'uber eats', r'dominos', r'pizza', 
                r'restaurant', r'cafe', r'coffee', r'food', r'grocery', 
                r'supermarket', r'kirana', r'bigbasket', r'milk', r'vegetable'
            ],
            'transportation': [
                r'uber', r'ola', r'cab', r'taxi', r'auto', r'metro', r'train', 
                r'bus', r'petrol', r'diesel', r'fuel', r'parking', r'rapido'
            ],
            'shopping': [
                r'amazon', r'flipkart', r'myntra', r'ajio', r'nykaa', r'shop', 
                r'store', r'mall', r'market', r'purchase', r'buy', r'retail'
            ],
            'utilities': [
                r'electricity', r'water', r'gas', r'bill', r'recharge', 
                r'mobile', r'phone', r'internet', r'broadband', r'wifi', 
                r'postpaid', r'prepaid', r'dth', r'utility', r'jio', r'airtel', r'vi',
                r'tata power', r'bses', r'mahanagar gas'
            ],
            'entertainment': [
                r'movie', r'netflix', r'prime', r'hotstar', r'disney', r'zee5', 
                r'sonyliv', r'theatre', r'cinema', r'ticket', r'concert', r'show',
                r'spotify', r'gaana', r'wynk', r'music'
            ],
            'health': [
                r'hospital', r'doctor', r'clinic', r'medical', r'medicine', 
                r'pharmacy', r'health', r'dental', r'eye', r'apollo', r'max', 
                r'medplus', r'netmeds', r'pharmeasy', r'1mg'
            ],
            'education': [
                r'school', r'college', r'university', r'course', r'class', 
                r'tuition', r'fee', r'book', r'stationery', r'udemy', r'coursera',
                r'edx', r'byju', r'unacademy', r'education'
            ],
            'travel': [
                r'flight', r'air', r'indigo', r'spicejet', r'hotel', r'resort', 
                r'booking', r'makemytrip', r'goibibo', r'oyo', r'travel', r'tour',
                r'holiday', r'vacation', r'irctc', r'railway'
            ],
            'housing': [
                r'rent', r'maintenance', r'society', r'apartment', r'flat', 
                r'house', r'property', r'loan', r'emi', r'mortgage', r'realty'
            ],
            'income': [
                r'salary', r'income', r'payment received', r'stipend', r'bonus', 
                r'interest', r'dividend', r'refund', r'reimbursement', r'credit'
            ],
            'investment': [
                r'mutual fund', r'share', r'stock', r'bond', r'debenture', r'fd', 
                r'fixed deposit', r'gold', r'zerodha', r'upstox', r'groww', 
                r'investment', r'sip', r'etf', r'nps', r'ppf'
            ],
            'bills': [
                r'bill payment', r'due', r'invoice', r'subscription', r'insurance',
                r'premium', r'tax', r'gst', r'emi', r'installment', r'payment'
            ]
        }
        
        self.vectorizer = None
        self.model = None
        self.model_ready = False
        
        self._load_model()
    
    def _preprocess_text(self, text):
        """Preprocess text for NLP"""
        if not text:
            return ""
        
        text = text.lower()
        
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(text)
        filtered_tokens = [w for w in tokens if w not in stop_words]
        
        return " ".join(filtered_tokens)
    
    def _rule_based_categorize(self, description):
        """Categorize transaction using rule-based approach"""
        if not description:
            return 'other'
        
        description = description.lower()
        
        for category, patterns in self.rules.items():
            for pattern in patterns:
                if re.search(pattern, description):
                    return category
        
        return None
    
    def _ml_based_categorize(self, description):
        """Categorize transaction using ML model"""
        if not self.model_ready or not description:
            return 'other'
        
        processed_desc = self._preprocess_text(description)
        
        X = self.vectorizer.transform([processed_desc])
        
        prediction = self.model.predict(X)
        
        return prediction[0]
    
    def categorize(self, transaction):
        """
        Categorize a transaction using rule-based approach first,
        falling back to ML-based approach if no rule matches
        """
        category = self._rule_based_categorize(transaction.description)
        
        if category is None and self.model_ready:
            category = self._ml_based_categorize(transaction.description)
        elif category is None:
            category = 'other'
        
        transaction.category = category
        return transaction
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        try:
            if os.path.exists('vectorizer.pkl') and os.path.exists('model.pkl'):
                with open('vectorizer.pkl', 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open('model.pkl', 'rb') as f:
                    self.model = pickle.load(f)
                self.model_ready = True
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model_ready = False
    
    def train_model(self, transactions, labels=None):
        """
        Train ML model using transaction data
        If labels are not provided, use rule-based categorization as ground truth
        """
        descriptions = []
        categories = []
        
        for transaction in transactions:
            if transaction.description:
                descriptions.append(transaction.description)
                
                if labels and transaction.id in labels:
                    categories.append(labels[transaction.id])
                else:
                    category = self._rule_based_categorize(transaction.description)
                    if category is None:
                        category = 'other'
                    categories.append(category)
        
        if len(descriptions) < 20: 
            print("Not enough data to train the model")
            return False
        
        processed_descriptions = [self._preprocess_text(desc) for desc in descriptions]
        
        X_train, X_test, y_train, y_test = train_test_split(
            processed_descriptions, categories, test_size=0.2, random_state=42
        )
        
        self.vectorizer = TfidfVectorizer(max_features=5000)
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        X_test_tfidf = self.vectorizer.transform(X_test)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train_tfidf, y_train)
        
        accuracy = self.model.score(X_test_tfidf, y_test)
        print(f"Model trained successfully with accuracy: {accuracy:.2f}")
        
        with open('vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)
        with open('model.pkl', 'wb') as f:
            pickle.dump(self.model, f)
        
        self.model_ready = True
        return True
    
    def bulk_categorize(self, transactions):
        """Categorize a list of transactions"""
        categorized_transactions = []
        
        for transaction in transactions:
            categorized_transaction = self.categorize(transaction)
            categorized_transactions.append(categorized_transaction)
        
        return categorized_transactions