from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import boto3
import uuid
import os
import hashlib
from datetime import datetime
from functools import wraps
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pickle-secret-key-2025')

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@pickles.com')

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)
ses = boto3.client('ses', region_name=AWS_REGION)

# DynamoDB tables
order_table = dynamodb.Table('PickleOrders')
user_table = dynamodb.Table('PickleUsers')
contact_table = dynamodb.Table('PickleContacts')

def hash_password(password):
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def send_email_notification(to_email, subject, message):
    """Send email via SNS and SES"""
    try:
        # Send via SNS
        if SNS_TOPIC_ARN:
            sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
        
        # Send via SES for direct email
        ses.send_email(
            Source=ADMIN_EMAIL,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': message}}
            }
        )
        return True
    except ClientError:
        return False

def get_instance_info():
    """Get EC2 instance metadata"""
    try:
        import urllib.request
        response = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id', timeout=2)
        return response.read().decode('utf-8')
    except:
        return 'local'

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            message = request.form['message']
            contact_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            # Save contact inquiry to DynamoDB
            contact_table.put_item(Item={
                'contact_id': contact_id,
                'name': name,
                'email': email,
                'message': message,
                'timestamp': timestamp,
                'status': 'new'
            })

            # Send email notifications
            admin_message = f"New Contact Inquiry\n\nFrom: {name}\nEmail: {email}\nMessage: {message}"
            customer_message = f"Dear {name},\n\nThank you for contacting us! We have received your message and will get back to you soon.\n\nYour Message: {message}\n\nBest regards,\nHomemade Pickles & Snacks Team"
            
            send_email_notification(ADMIN_EMAIL, 'New Contact Inquiry', admin_message)
            send_email_notification(email, 'Thank you for contacting us', customer_message)
            
            flash('Thank you for contacting us! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'Message sending failed: {str(e)}', 'error')
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['username']
            password = request.form['password']
            hashed_password = hash_password(password)

            # Check user in DynamoDB
            response = user_table.get_item(Key={'email': email})
            if 'Item' in response:
                stored_password = response['Item'].get('password')
                if stored_password == hashed_password:
                    session['user_email'] = email
                    session['user_name'] = response['Item'].get('name')
                    return redirect(url_for('home'))
            
            flash('Invalid email or password', 'error')
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    return render_template('login.html')

@app.route('/create_test_user')
def create_test_user():
    try:
        hashed_password = hash_password('test123')
        user_table.put_item(Item={
            'email': 'test@test.com', 
            'name': 'testuser', 
            'password': hashed_password,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        })
        return 'Test user created: email=test@test.com, password=test123'
    except ClientError as e:
        return f'Error: {e}'

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            name = request.form['fullname']
            email = request.form['email']
            password = request.form['password']
            hashed_password = hash_password(password)
            timestamp = datetime.utcnow().isoformat()

            # Check if user already exists
            response = user_table.get_item(Key={'email': email})
            if 'Item' in response:
                flash('User already exists', 'error')
                return render_template('signup.html')

            # Save user to DynamoDB
            user_table.put_item(Item={
                'email': email,
                'name': name,
                'password': hashed_password,
                'created_at': timestamp,
                'status': 'active'
            })

            # Send welcome email
            welcome_message = f"Dear {name},\n\nWelcome to Homemade Pickles & Snacks!\n\nYour account has been created successfully. You can now login and start ordering our delicious homemade pickles and snacks.\n\nThank you for joining us!\n\nBest regards,\nHomemade Pickles & Snacks Team"
            send_email_notification(email, 'Welcome to Homemade Pickles & Snacks!', welcome_message)
            
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Signup failed: {str(e)}', 'error')
    return render_template('signup.html')

@app.route('/order-success')
@login_required
def order_success():
    return render_template('order_success.html')

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        try:
            name = request.form['fullName']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            notes = request.form.get('notes', '')
            order_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            # Save checkout details to DynamoDB
            order_table.put_item(Item={
                'order_id': order_id,
                'name': name,
                'email': email,
                'phone': phone,
                'address': address,
                'notes': notes,
                'timestamp': timestamp,
                'status': 'checkout_completed',
                'source': 'checkout'
            })

            # Send confirmation emails
            customer_message = f"Dear {name},\n\nYour checkout is complete!\n\nOrder ID: {order_id}\nWe'll process your order and contact you soon.\n\nThank you!"
            send_email_notification(email, 'Checkout Confirmation', customer_message)
            
            session['last_order_id'] = order_id
            return redirect(url_for('order_success'))
        except Exception as e:
            flash(f'Checkout failed: {str(e)}', 'error')
    return render_template('checkout.html')

@app.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            city = request.form.get('city', '')
            pincode = request.form.get('pincode', '')
            item = request.form['item']
            quantity = int(request.form['quantity'])
            notes = request.form.get('notes', '')
            order_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            # Save to DynamoDB with full order details
            order_table.put_item(Item={
                'order_id': order_id,
                'name': name,
                'email': email,
                'phone': phone,
                'address': address,
                'city': city,
                'pincode': pincode,
                'item': item,
                'quantity': quantity,
                'notes': notes,
                'timestamp': timestamp,
                'status': 'pending',
                'total_amount': quantity * 100,  # Sample pricing
                'source': 'order_form'
            })

            # Send email notifications
            customer_message = f"Dear {name},\n\nYour order has been placed successfully!\n\nOrder ID: {order_id}\nItem: {item}\nQuantity: {quantity}\n\nWe'll contact you soon for delivery details.\n\nThank you for choosing Homemade Pickles & Snacks!"
            admin_message = f"New Order Received!\n\nOrder ID: {order_id}\nCustomer: {name}\nEmail: {email}\nPhone: {phone}\nItem: {item}\nQuantity: {quantity}\nAddress: {address}, {city} - {pincode}\nNotes: {notes}"
            
            send_email_notification(email, 'Order Confirmation - Homemade Pickles & Snacks', customer_message)
            send_email_notification(ADMIN_EMAIL, f'New Order - {order_id}', admin_message)

            session['last_order_id'] = order_id
            return redirect(url_for('order_success'))
        except Exception as e:
            flash(f'Order processing failed: {str(e)}', 'error')
            return render_template('order.html')
    return render_template('order.html')

@app.route('/snackes')
@login_required
def snackes():
    return render_template('snackes.html')

@app.route('/notify')
def notify():
    # Send a sample SNS message
    if SNS_TOPIC_ARN:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message='A new order was received on Homemade Pickles & Snacks!',
            Subject='New Pickle Order Alert'
        )
    return "SNS notification sent!"

@app.route('/aws-info')
def aws_info():
    """Display AWS service information"""
    try:
        # Get EC2 instance info
        instance_id = get_instance_info()
        
        # Get IAM role info
        try:
            sts = boto3.client('sts', region_name=AWS_REGION)
            identity = sts.get_caller_identity()
            account_id = identity['Account']
            role_arn = identity.get('Arn', 'No role attached')
        except:
            account_id = 'Unknown'
            role_arn = 'No role attached'
        
        # Test DynamoDB connectivity
        try:
            user_table.describe_table()
            dynamodb_status = 'Connected'
        except:
            dynamodb_status = 'Error'
            
        # Test SNS connectivity
        try:
            if SNS_TOPIC_ARN:
                sns.get_topic_attributes(TopicArn=SNS_TOPIC_ARN)
                sns_status = 'Connected'
            else:
                sns_status = 'Not Configured'
        except:
            sns_status = 'Error'
        
        info = {
            'instance_id': instance_id,
            'account_id': account_id,
            'role_arn': role_arn,
            'region': AWS_REGION,
            'dynamodb_status': dynamodb_status,
            'sns_status': sns_status,
            'tables': ['PickleUsers', 'PickleOrders', 'PickleContacts']
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    try:
        # Test database connectivity
        user_table.describe_table()
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/test-email')
def test_email():
    """Test email functionality"""
    try:
        test_message = f"Test email sent at {datetime.utcnow().isoformat()}"
        result = send_email_notification(ADMIN_EMAIL, 'Test Email', test_message)
        return jsonify({'email_sent': result, 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/veg_pickles')
@login_required
def veg_pickles():
    return render_template('veg_pickles.html')

@app.route('/non_veg_pickles')
@login_required
def non_veg_pickles():
    return render_template('non_veg_pickles.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
