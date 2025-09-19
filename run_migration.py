#!/usr/bin/env python3
"""
Simple migration script to create tracker tables
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text

# Create a minimal Flask app for migration
app = Flask(__name__)

# Configure database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://mariadb:0cZ0FRFBB1UPsmnTKjGfm8iofaBkb0s7JZAggtz1f3RGnqqnu7d2h6dk6zF8EGbv@104.248.150.75:33004/default')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

def create_tracker_tables():
    """Create the tracker tables using SQL"""

    # Read the SQL migration file
    with open('tracker_migration.sql', 'r') as f:
        sql_commands = f.read()

    print("Executing tracker table creation...")

    try:
        # Execute the SQL commands
        with app.app_context():
            with db.engine.connect() as conn:
                # Split into individual commands and execute
                commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]

                for command in commands:
                    if command:
                        conn.execute(text(command))

                conn.commit()

        print("✅ Tracker tables created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating tracker tables: {e}")
        return False

if __name__ == "__main__":
    create_tracker_tables()