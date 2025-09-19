#!/usr/bin/env python3
"""
Simple migration script using pymysql directly
"""

import pymysql
import os
import sys

def run_migration():
    """Run the tracker migration using pymysql"""

    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    try:
        # Parse the database URL
        if db_url.startswith('mysql+pymysql://'):
            db_url = db_url[len('mysql+pymysql://'):]

        # Split the URL
        parts = db_url.split('@')
        if len(parts) != 2:
            raise ValueError("Invalid DATABASE_URL format")

        # Parse user:password
        user_pass = parts[0]
        host_db = parts[1]

        if '@' in user_pass:
            raise ValueError("Invalid user:password format")

        # Extract username and password
        if ':' in user_pass:
            username, password = user_pass.split(':', 1)
        else:
            username = user_pass
            password = ''

        # Parse host:port/database
        if '/' not in host_db:
            raise ValueError("Invalid host/database format")

        host_port_part, database = host_db.split('/', 1)

        # Parse host and port
        if ':' in host_port_part:
            host, port_str = host_port_part.split(':', 1)
            port = int(port_str)
        else:
            host = host_port_part
            port = 3306

        print(f"Connecting to {host}:{port} as {username}...")

        # Connect to database
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            port=port,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("Connected successfully!")

        # Read the migration SQL
        with open('tracker_migration.sql', 'r') as f:
            sql_content = f.read()

        # Execute the migration
        with connection.cursor() as cursor:
            # Split into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            print(f"Executing {len(statements)} SQL statements...")

            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"  {i}. {statement[:50]}...")
                    cursor.execute(statement)

            # Commit all changes
            connection.commit()
            print("All statements executed successfully!")

        # Verify tables were created
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [list(table.values())[0] for table in tables]

            print(f"\nTables in database:")
            for table in sorted(table_names):
                marker = "✓" if table in ['peptide_cycle', 'dosage_log', 'progress_entry'] else " "
                print(f"{marker} {table}")

            # Check if our tracker tables were created
            tracker_tables = ['peptide_cycle', 'dosage_log', 'progress_entry']
            created_tables = [t for t in tracker_tables if t in table_names]

            if len(created_tables) == len(tracker_tables):
                print(f"\n✅ All {len(tracker_tables)} tracker tables created successfully!")
                success = True
            else:
                missing = [t for t in tracker_tables if t not in table_names]
                print(f"\n❌ Missing tables: {missing}")
                success = False

        connection.close()
        return success

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)