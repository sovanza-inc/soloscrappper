from flask import Flask, request, jsonify
import stripe
import os
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
from config import Config

# Initialize Flask app
app = Flask(__name__)

# Configure Stripe
stripe.api_key = Config.STRIPE_SECRET_KEY

# Database configuration
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_4GvhMte9BIoW@ep-mute-waterfall-ad00hkay-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Email configuration
SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465
SMTP_USERNAME = "support@soloscraper.com"
SMTP_PASSWORD = "Soloscraper4565!@"

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(DB_CONNECTION_STRING)
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def generate_license_key() -> str:
    """Generate a unique license key with dynamic year and suffix combinations"""
    import random
    import string
    
    # Generate random year (2029-2035)
    year = random.randint(2029, 2035)
    
    # Generate random 4-digit suffix
    suffix = ''.join(random.choices(string.digits, k=4))
    
    # Format: TEST-LICENSE-KEY-YYYY-XXXX
    license_key = f"TEST-LICENSE-KEY-{year}-{suffix}"
    
    return license_key

def insert_license_to_db(license_key: str, customer_email: str) -> bool:
    """Insert new license into the database"""
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Failed to connect to database")
            return False
        
        cursor = conn.cursor()
        
        # Set expiration date to 1 year from now
        expires_at = datetime.now() + timedelta(days=365)
        
        # Insert new license
        cursor.execute("""
            INSERT INTO licenses (key, machine_id, valid, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (
            license_key,
            None,  # machine_id (will be set when user activates)
            True,  # valid
            expires_at
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ License key {license_key} inserted into database")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting license to database: {e}")
        return False

def send_license_email(customer_email: str, customer_name: str, license_key: str) -> bool:
    """Send license key to customer via email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = customer_email
        msg['Subject'] = "🎉 Your SoloScraper License Key"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">🎉 Welcome to SoloScraper!</h2>
                
                <p>Dear {customer_name or 'Valued Customer'},</p>
                
                <p>Thank you for your purchase! Your payment has been processed successfully.</p>
                
                <div style="background: #f8f9fa; border: 2px solid #28a745; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                    <h3 style="color: #28a745; margin: 0 0 10px 0;">Your License Key</h3>
                    <div style="background: #fff; border: 1px solid #ddd; border-radius: 4px; padding: 15px; font-family: monospace; font-size: 18px; font-weight: bold; color: #2c3e50;">
                        {license_key}
                    </div>
                </div>
                
                <h3>📋 How to Activate:</h3>
                <ol>
                    <li>Open SoloScraper application</li>
                    <li>Click on "Activate License" or "Enter License Key"</li>
                    <li>Enter the license key above</li>
                    <li>Click "Activate"</li>
                </ol>
                
                <h3>🔑 License Details:</h3>
                <ul>
                    <li><strong>License Key:</strong> {license_key}</li>
                    <li><strong>Valid Until:</strong> {(datetime.now() + timedelta(days=365)).strftime('%B %d, %Y')}</li>
                    <li><strong>Activation:</strong> One machine per license</li>
                </ul>
                
                <div style="background: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>💡 Pro Tip:</strong> Keep this email safe! You'll need this license key to activate your SoloScraper software.</p>
                </div>
                
                <p>If you have any questions or need support, please contact us at <a href="mailto:support@soloscraper.com">support@soloscraper.com</a></p>
                
                <p>Happy Scraping! 🚀</p>
                
                <p>Best regards,<br>
                <strong>The SoloScraper Team</strong></p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="text-align: center; color: #666; font-size: 12px;">
                    This is an automated email. Please do not reply to this message.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ License key email sent to {customer_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def print_payment_success_info(event_data):
    """Print detailed payment success information to terminal"""
    print("\n" + "="*80)
    print("🎉 STRIPE PAYMENT SUCCESSFUL! 🎉")
    print("="*80)
    
    # Extract relevant information
    payment_intent = event_data.get('data', {}).get('object', {})
    
    print(f"💰 Payment Amount: ${payment_intent.get('amount', 0) / 100:.2f}")
    print(f"💳 Payment Status: {payment_intent.get('status', 'Unknown')}")
    print(f"🆔 Payment Intent ID: {payment_intent.get('id', 'Unknown')}")
    print(f"📅 Created At: {datetime.fromtimestamp(payment_intent.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Customer information
    customer_id = payment_intent.get('customer')
    if customer_id:
        try:
            customer = stripe.Customer.retrieve(customer_id)
            print(f"\n👤 CUSTOMER INFORMATION:")
            print(f"   Customer ID: {customer.id}")
            print(f"   Email: {customer.email or 'Not provided'}")
            print(f"   Name: {customer.name or 'Not provided'}")
            print(f"   Phone: {customer.phone or 'Not provided'}")
            
            # Address information
            if customer.address:
                addr = customer.address
                print(f"   Address: {addr.get('line1', '')} {addr.get('line2', '')}")
                print(f"   City: {addr.get('city', '')}")
                print(f"   State: {addr.get('state', '')}")
                print(f"   Postal Code: {addr.get('postal_code', '')}")
                print(f"   Country: {addr.get('country', '')}")
        except Exception as e:
            print(f"   Error retrieving customer info: {e}")
    
    # Payment method information
    payment_method_id = payment_intent.get('payment_method')
    if payment_method_id:
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            print(f"\n💳 PAYMENT METHOD:")
            print(f"   Type: {payment_method.type}")
            if payment_method.type == 'card':
                card = payment_method.card
                print(f"   Brand: {card.brand}")
                print(f"   Last 4: {card.last4}")
                print(f"   Exp Month: {card.exp_month}")
                print(f"   Exp Year: {card.exp_year}")
        except Exception as e:
            print(f"   Error retrieving payment method info: {e}")
    
    # Product information
    print(f"\n🛍️ PRODUCT INFORMATION:")
    print(f"   Product ID: {Config.PRODUCT_ID}")
    print(f"   Price ID: {Config.PRICE_ID}")
    
    print("="*80)
    print("✅ Webhook processed successfully!")
    print("="*80 + "\n")

def process_payment_success(event_data):
    """Process successful payment and create license"""
    try:
        payment_intent = event_data.get('data', {}).get('object', {})
        payment_intent_id = payment_intent.get('id')
        
        # Get customer information
        customer_id = payment_intent.get('customer')
        customer_email = None
        customer_name = None
        
        if customer_id:
            try:
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.email
                customer_name = customer.name
            except Exception as e:
                print(f"❌ Error retrieving customer info: {e}")
                return False
        
        if not customer_email:
            print("❌ No customer email found, cannot create license")
            return False
        
        # Generate license key
        license_key = generate_license_key()
        print(f"🔑 Generated license key: {license_key}")
        
        # Insert into database
        if insert_license_to_db(license_key, customer_email):
            print(f"💾 License saved to database for {customer_email}")
            
            # Send email
            if send_license_email(customer_email, customer_name, license_key):
                print(f"📧 License key email sent successfully to {customer_email}")
                return True
            else:
                print(f"❌ Failed to send email to {customer_email}")
                return False
        else:
            print(f"❌ Failed to save license to database")
            return False
            
    except Exception as e:
        print(f"❌ Error processing payment success: {e}")
        return False

@app.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(f"❌ Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    event_type = event['type']
    print(f"📨 Received webhook event: {event_type}")
    
    if event_type == 'payment_intent.succeeded':
        print_payment_success_info(event)
        
        # Process payment success and create license
        if process_payment_success(event):
            print("🎉 License creation and email sending completed successfully!")
        else:
            print("❌ License creation or email sending failed")
        
        return jsonify({'status': 'success', 'message': 'Payment success processed'})
    
    elif event_type == 'payment_intent.payment_failed':
        print(f"❌ Payment failed: {event['data']['object']['id']}")
        return jsonify({'status': 'success', 'message': 'Payment failure processed'})
    
    elif event_type == 'checkout.session.completed':
        print(f"✅ Checkout session completed: {event['data']['object']['id']}")
        return jsonify({'status': 'success', 'message': 'Checkout completed processed'})
    
    else:
        print(f"ℹ️ Unhandled event type: {event_type}")
        return jsonify({'status': 'success', 'message': 'Event received'})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Stripe Webhook API with License Generation',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test-payment', methods=['GET'])
def test_payment_info():
    """Test endpoint to show payment link and product info"""
    return jsonify({
        'payment_link': Config.PAYMENT_LINK,
        'product_id': Config.PRODUCT_ID,
        'price_id': Config.PRICE_ID,
        'webhook_url': Config.WEBHOOK_URL,
        'message': 'Use the payment link to test the webhook and license generation'
    })

if __name__ == '__main__':
    print("🚀 Starting Stripe Webhook API with License Generation...")
    Config.print_config()
    print("="*80)
    print("💡 This API now generates license keys and sends them via email")
    print("💡 To test locally, use ngrok or similar to expose your local server")
    print("💡 Update the webhook URL in Stripe dashboard to point to your local endpoint")
    print("="*80)
    
    # Run the Flask app
    app.run(
        debug=Config.FLASK_DEBUG, 
        host=Config.FLASK_HOST, 
        port=Config.FLASK_PORT
    )
