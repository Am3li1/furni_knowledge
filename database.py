# database.py - UPDATED with better error handling
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

# Get connection string from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Get a database connection with better error handling"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in environment variables. Check your .env file")
    
    # Clean up the connection string
    db_url = DATABASE_URL.strip()
    
    # Fix common issues
    if db_url.startswith('"') and db_url.endswith('"'):
        db_url = db_url[1:-1]  # Remove quotes if present
    
    if db_url.startswith("postgresql:postgresql://"):
        # Fix double prefix issue
        db_url = db_url.replace("postgresql:postgresql://", "postgresql://", 1)
    
    print(f"Connecting to: {db_url[:50]}...")  # Print first 50 chars for debugging
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        print("✅ Database connection successful!")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Connection string used: {db_url[:80]}...")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def init_database():
    """Initialize database tables with better error messages"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic query first
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version[0]}")
        
        # Your existing table creation code here...
        # (Keep all the CREATE TABLE statements from before)
        
        # 1. Rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'rooms' table")
        
        # 2. Furniture types table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS furniture_types (
                id SERIAL PRIMARY KEY,
                room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(room_id, name)
            )
        ''')
        print("✅ Created 'furniture_types' table")
        
        # 3. Product configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_configs (
                id SERIAL PRIMARY KEY,
                furniture_type_id INTEGER REFERENCES furniture_types(id) ON DELETE CASCADE,
                config_name VARCHAR(200) NOT NULL,
                attributes JSONB DEFAULT '{}',
                options JSONB DEFAULT '{}',
                price_range VARCHAR(100),
                delivery_time VARCHAR(50),
                customizations TEXT,
                images TEXT[] DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'product_configs' table")
        
        # 4. Conversation flow table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_flow (
                id SERIAL PRIMARY KEY,
                step_name VARCHAR(100) UNIQUE NOT NULL,
                question_text TEXT NOT NULL,
                button_type VARCHAR(50) DEFAULT 'single_select',
                options JSONB NOT NULL,
                next_step_map JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'conversation_flow' table")
        
        # 5. Admin interview sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id SERIAL PRIMARY KEY,
                session_data JSONB,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'admin_sessions' table")
        
        # 6. Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'admin_users' table")
        
        # 7. Customer sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                selections JSONB DEFAULT '{}',
                current_step VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'customer_sessions' table")
        
        conn.commit()
        print("🎉 All database tables created successfully!")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error during database initialization: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check your .env file has DATABASE_URL")
        print("2. Check the Neon connection string format")
        print("3. Make sure Neon database is running")
        print("4. Check internet connection")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

# Helper function to test connection
def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("✅ Connection test passed!")
        init_database()
    else:
        print("❌ Connection test failed. Check your .env file and Neon settings.")