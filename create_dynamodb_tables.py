#!/usr/bin/env python3
"""
DynamoDB table creation script
Creates all required tables for the application
"""

import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def create_table(table_name, key_schema, attribute_definitions, billing_mode='PAY_PER_REQUEST'):
    """Create a DynamoDB table"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode=billing_mode
        )
        
        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"✅ Table {table_name} created successfully!")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return True
        else:
            print(f"❌ Error creating table {table_name}: {e}")
            return False

def create_all_tables():
    """Create all required DynamoDB tables"""
    print("🗄️  Creating DynamoDB Tables...")
    print("=" * 50)
    
    tables = [
        {
            'name': 'PickleUsers',
            'key_schema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
            'attributes': [{'AttributeName': 'email', 'AttributeType': 'S'}]
        },
        {
            'name': 'PickleOrders',
            'key_schema': [{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            'attributes': [{'AttributeName': 'order_id', 'AttributeType': 'S'}]
        },
        {
            'name': 'PickleContacts',
            'key_schema': [{'AttributeName': 'contact_id', 'KeyType': 'HASH'}],
            'attributes': [{'AttributeName': 'contact_id', 'AttributeType': 'S'}]
        }
    ]
    
    results = []
    for table_config in tables:
        result = create_table(
            table_config['name'],
            table_config['key_schema'],
            table_config['attributes']
        )
        results.append(result)
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tables created successfully!")
        print("\nTable Details:")
        for table_config in tables:
            print(f"📋 {table_config['name']}")
            print(f"   Primary Key: {table_config['key_schema'][0]['AttributeName']}")
    else:
        print("⚠️  Some tables failed to create. Check AWS credentials and permissions.")
    
    return all(results)

def verify_tables():
    """Verify all tables exist and are active"""
    print("\n🔍 Verifying Tables...")
    
    table_names = ['PickleUsers', 'PickleOrders', 'PickleContacts']
    
    for table_name in table_names:
        try:
            table = dynamodb.Table(table_name)
            response = table.describe_table()
            status = response['Table']['TableStatus']
            print(f"✅ {table_name}: {status}")
        except ClientError as e:
            print(f"❌ {table_name}: Error - {e}")

def main():
    """Main function"""
    print("🚀 DynamoDB Table Setup")
    print("=" * 50)
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts', region_name=AWS_REGION)
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"Region: {AWS_REGION}")
        print()
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        return
    
    # Create tables
    success = create_all_tables()
    
    if success:
        verify_tables()
        print("\n🎉 DynamoDB setup complete!")
        print("Your application is ready to use DynamoDB!")
    else:
        print("\n❌ DynamoDB setup failed!")
        print("Please check your AWS credentials and permissions.")

if __name__ == "__main__":
    main()