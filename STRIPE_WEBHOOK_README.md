# Stripe Webhook API

A Flask-based API that handles Stripe webhooks and displays detailed user information when payments are successful.

## 🚀 Features

- **Automatic Payment Detection**: Listens for Stripe webhook events
- **Detailed User Information**: Displays customer details, payment method, and transaction info
- **Real-time Terminal Output**: Shows payment success information in the console
- **Secure Webhook Verification**: Validates webhook signatures from Stripe
- **Multiple Event Support**: Handles payment success, failure, and checkout completion

## 📋 Prerequisites

- Python 3.7+
- Stripe account with test keys
- Product and price configured in Stripe

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   - Copy `env_template.txt` to `.env`
   - Update the values in `.env` with your actual Stripe credentials

3. **Stripe Configuration**:
   - Ensure your webhook endpoint is configured in Stripe Dashboard
   - Set webhook URL to: `https://soloscraper.com/api/webhook`
   - Add webhook secret to your environment variables

## 🔧 Configuration

The API uses the following configuration (from `config.py`):

- **Stripe Keys**: Secret key, publishable key, and webhook secret
- **Product Details**: Product ID and price ID
- **Payment Link**: Your Stripe checkout link
- **Flask Settings**: Host, port, and debug mode

## 🚀 Running the API

### Local Development
```bash
python stripe_webhook_api.py
```

The API will start on `http://localhost:5000`

### Production Deployment
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
python stripe_webhook_api.py
```

## 🌐 API Endpoints

### 1. Webhook Endpoint
- **URL**: `/api/webhook`
- **Method**: `POST`
- **Purpose**: Receives Stripe webhook events
- **Authentication**: Stripe signature verification

### 2. Health Check
- **URL**: `/api/health`
- **Method**: `GET`
- **Purpose**: API health status

### 3. Test Payment Info
- **URL**: `/api/test-payment`
- **Method**: `GET`
- **Purpose**: Display payment link and product information

## 🔗 Testing the Webhook

### Option 1: Use Stripe CLI (Recommended)
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:5000/api/webhook

# In another terminal, trigger a test payment
stripe trigger payment_intent.succeeded
```

### Option 2: Use ngrok for Local Testing
```bash
# Install ngrok
ngrok http 5000

# Update webhook URL in Stripe Dashboard to your ngrok URL
# Example: https://abc123.ngrok.io/api/webhook
```

### Option 3: Use Your Payment Link
1. Visit: `https://buy.stripe.com/test_3cI4gzgoe5Nu6qz14je3e00`
2. Complete a test payment
3. Check your terminal for webhook output

## 📊 Webhook Events Handled

### Payment Success (`payment_intent.succeeded`)
- ✅ Payment amount and status
- 👤 Customer information (ID, email, name, phone)
- 🏠 Customer address details
- 💳 Payment method information
- 🛍️ Product and price details

### Payment Failure (`payment_intent.payment_failed`)
- ❌ Payment failure notification
- 🔍 Payment intent ID

### Checkout Completion (`checkout.session.completed`)
- ✅ Checkout session completion
- 🔍 Session ID

## 🔒 Security Features

- **Webhook Signature Verification**: Ensures webhooks come from Stripe
- **Environment Variable Configuration**: Secure credential management
- **Input Validation**: Validates all incoming webhook data

## 📝 Environment Variables

Create a `.env` file with the following variables:

```env
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
PRODUCT_ID=prod_your_product_id
PRICE_ID=price_your_price_id
PAYMENT_LINK=https://buy.stripe.com/your_payment_link
WEBHOOK_URL=https://yourdomain.com/api/webhook
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## 🐛 Troubleshooting

### Common Issues

1. **Webhook Signature Verification Failed**
   - Check webhook secret in Stripe Dashboard
   - Ensure webhook secret matches your `.env` file

2. **No Webhook Events Received**
   - Verify webhook URL in Stripe Dashboard
   - Check if your server is accessible from the internet
   - Use ngrok for local testing

3. **Payment Information Not Displayed**
   - Ensure webhook events are being sent to the correct endpoint
   - Check Stripe Dashboard for webhook delivery status

### Debug Mode
Enable debug mode to see detailed logs:
```bash
export FLASK_DEBUG=True
```

## 📱 Example Output

When a payment is successful, you'll see output like this:

```
================================================================================
🎉 STRIPE PAYMENT SUCCESSFUL! 🎉
================================================================================
💰 Payment Amount: $29.99
💳 Payment Status: succeeded
🆔 Payment Intent ID: pi_1234567890abcdef
📅 Created At: 2024-01-15 14:30:25

👤 CUSTOMER INFORMATION:
   Customer ID: cus_1234567890abcdef
   Email: customer@example.com
   Name: John Doe
   Phone: +1234567890
   Address: 123 Main St
   City: New York
   State: NY
   Postal Code: 10001
   Country: US

💳 PAYMENT METHOD:
   Type: card
   Brand: visa
   Last 4: 4242
   Exp Month: 12
   Exp Year: 2025

🛍️ PRODUCT INFORMATION:
   Product ID: prod_SvXJsNpsCxwnls
   Price ID: price_1RzgEeFaG3nZ4nVpjiSCwpdA
================================================================================
✅ Webhook processed successfully!
================================================================================
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Stripe webhook documentation
3. Check Flask application logs
4. Verify webhook configuration in Stripe Dashboard

## 🔗 Useful Links

- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Stripe CLI Installation](https://stripe.com/docs/stripe-cli)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [ngrok Documentation](https://ngrok.com/docs)
