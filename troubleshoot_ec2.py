#!/usr/bin/env python3
"""
EC2 Troubleshooting Script
Diagnoses common issues with Flask app deployment on EC2
"""

import subprocess
import socket
import requests
import os
import sys

def run_command(command):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check Python installation"""
    print("🐍 Checking Python...")
    success, stdout, stderr = run_command("python3 --version")
    if success:
        print(f"✅ Python: {stdout.strip()}")
        return True
    else:
        print("❌ Python 3 not installed")
        return False

def check_pip():
    """Check pip installation"""
    print("📦 Checking pip...")
    success, stdout, stderr = run_command("pip3 --version")
    if success:
        print(f"✅ pip: {stdout.strip()}")
        return True
    else:
        print("❌ pip3 not installed")
        return False

def check_dependencies():
    """Check required Python packages"""
    print("📚 Checking dependencies...")
    packages = ['flask', 'boto3', 'python-dotenv']
    all_installed = True
    
    for package in packages:
        success, stdout, stderr = run_command(f"pip3 show {package}")
        if success:
            print(f"✅ {package}: installed")
        else:
            print(f"❌ {package}: not installed")
            all_installed = False
    
    return all_installed

def check_port(port=5000):
    """Check if port is available"""
    print(f"🔌 Checking port {port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port}: in use (app might be running)")
            return True
        else:
            print(f"⚠️  Port {port}: available (app not running)")
            return False
    except Exception as e:
        print(f"❌ Port check failed: {e}")
        return False

def check_firewall():
    """Check firewall settings"""
    print("🔥 Checking firewall...")
    success, stdout, stderr = run_command("sudo firewall-cmd --list-ports")
    if success:
        if "5000/tcp" in stdout:
            print("✅ Firewall: Port 5000 is open")
            return True
        else:
            print("❌ Firewall: Port 5000 is not open")
            return False
    else:
        print("⚠️  Could not check firewall (might not be running)")
        return True

def check_security_group():
    """Check EC2 security group"""
    print("🛡️  Security Group Check:")
    print("   Make sure your EC2 security group allows:")
    print("   - Inbound: Port 5000 (TCP) from 0.0.0.0/0")
    print("   - Inbound: Port 80 (HTTP) from 0.0.0.0/0")
    print("   - Inbound: Port 22 (SSH) from your IP")

def check_aws_credentials():
    """Check AWS credentials"""
    print("🔑 Checking AWS credentials...")
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        return False

def check_dynamodb_tables():
    """Check DynamoDB tables"""
    print("🗄️  Checking DynamoDB tables...")
    try:
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        tables = ['PickleUsers', 'PickleOrders', 'PickleContacts']
        all_exist = True
        
        for table_name in tables:
            try:
                table = dynamodb.Table(table_name)
                table.describe_table()
                print(f"✅ Table {table_name}: exists")
            except Exception as e:
                print(f"❌ Table {table_name}: missing")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ DynamoDB check failed: {e}")
        return False

def check_service_status():
    """Check systemd service status"""
    print("⚙️  Checking service status...")
    success, stdout, stderr = run_command("sudo systemctl status pickles-app")
    if success:
        if "active (running)" in stdout:
            print("✅ Service: running")
            return True
        else:
            print("❌ Service: not running")
            print("Service output:", stdout)
            return False
    else:
        print("❌ Service: not found or error")
        return False

def check_logs():
    """Check application logs"""
    print("📋 Checking logs...")
    success, stdout, stderr = run_command("sudo journalctl -u pickles-app --no-pager -n 20")
    if success:
        print("Recent logs:")
        print(stdout)
    else:
        print("❌ Could not retrieve logs")

def test_application():
    """Test application endpoints"""
    print("🧪 Testing application...")
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        print(f"✅ App responds: Status {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ App not responding: {e}")
        return False

def provide_solutions():
    """Provide common solutions"""
    print("\n" + "="*50)
    print("🔧 COMMON SOLUTIONS:")
    print("="*50)
    
    print("\n1. Install missing dependencies:")
    print("   pip3 install --user flask boto3 python-dotenv")
    
    print("\n2. Create DynamoDB tables:")
    print("   python3 create_dynamodb_tables.py")
    
    print("\n3. Open firewall port:")
    print("   sudo firewall-cmd --permanent --add-port=5000/tcp")
    print("   sudo firewall-cmd --reload")
    
    print("\n4. Start the service:")
    print("   sudo systemctl start pickles-app")
    print("   sudo systemctl enable pickles-app")
    
    print("\n5. Check service logs:")
    print("   sudo journalctl -u pickles-app -f")
    
    print("\n6. Run app manually for debugging:")
    print("   cd /path/to/your/app")
    print("   python3 home/app.py")

def main():
    """Main troubleshooting function"""
    print("🔍 EC2 Flask App Troubleshooting")
    print("="*50)
    
    checks = [
        ("Python Installation", check_python),
        ("Pip Installation", check_pip),
        ("Dependencies", check_dependencies),
        ("Port Availability", check_port),
        ("Firewall", check_firewall),
        ("AWS Credentials", check_aws_credentials),
        ("DynamoDB Tables", check_dynamodb_tables),
        ("Service Status", check_service_status),
        ("Application Response", test_application),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        result = check_func()
        results.append((name, result))
    
    # Show security group info
    print(f"\nSecurity Group:")
    check_security_group()
    
    # Show logs if service is not working
    if not any(result for name, result in results if "Service" in name):
        check_logs()
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    print("="*50)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    failed_checks = [name for name, result in results if not result]
    
    if failed_checks:
        print(f"\n⚠️  Failed checks: {len(failed_checks)}")
        provide_solutions()
    else:
        print("\n🎉 All checks passed! Your app should be working.")

if __name__ == "__main__":
    main()