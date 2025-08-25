import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Stripe Webhook API"""
    
    # Stripe Configuration
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Product Configuration
    PRODUCT_ID = os.getenv('PRODUCT_ID')
    PRICE_ID = os.getenv('PRICE_ID')
    
    # Payment Link
    PAYMENT_LINK = os.getenv('PAYMENT_LINK')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    
    # Webhook Configuration
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("🔧 Current Configuration:")
        print(f"   Product ID: {cls.PRODUCT_ID}")
        print(f"   Price ID: {cls.PRICE_ID}")
        print(f"   Payment Link: {cls.PAYMENT_LINK}")
        print(f"   Webhook URL: {cls.WEBHOOK_URL}")
        print(f"   Flask Host: {cls.FLASK_HOST}")
        print(f"   Flask Port: {cls.FLASK_PORT}")
        print(f"   Debug Mode: {cls.FLASK_DEBUG}")
        print(f"   Environment: {cls.FLASK_ENV}")
