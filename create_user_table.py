import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_user_table():
    """Create the user table directly using PyMySQL"""

    # Get database connection details from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        return

    # Parse the database URL (format: mysql+pymysql://user:pass@host:port/database)
    try:
        # Remove the mysql+pymysql:// prefix
        if db_url.startswith('mysql+pymysql://'):
            db_url = db_url[len('mysql+pymysql://'):]

        # Split into parts
        parts = db_url.split('@')
        if len(parts) != 2:
            raise ValueError("Invalid DATABASE_URL format")

        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')

        if len(user_pass) != 2:
            raise ValueError("Invalid user:password format")

        username = user_pass[0]
        password = user_pass[1]

        host_port = host_db[0].split(':')
        if len(host_port) == 2:
            host = host_port[0]
            port = int(host_port[1])
        else:
            host = host_port[0]
            port = 3306

        database = host_db[1]

        print(f"Connecting to database: {database} at {host}:{port}")

        # Create connection
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            port=port,
            database=database
        )

        print("Connected successfully!")

        # Create cursor
        cursor = connection.cursor()

        # Create user table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS `user` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `google_id` VARCHAR(100) UNIQUE NOT NULL,
            `email` VARCHAR(120) UNIQUE NOT NULL,
            `name` VARCHAR(100) NOT NULL,
            `picture` VARCHAR(200),
            `role` VARCHAR(20) DEFAULT 'student',
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `last_login` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        cursor.execute(create_table_sql)
        print("User table created successfully!")

        # Verify table exists
        cursor.execute("SHOW TABLES LIKE 'user'")
        result = cursor.fetchone()
        if result:
            print("✓ User table exists in database")
        else:
            print("✗ User table not found")

        # Show table structure
        cursor.execute("DESCRIBE `user`")
        print("\nTable structure:")
        for row in cursor.fetchall():
            print(f"  {row}")

        # Close connections
        cursor.close()
        connection.close()
        print("\nDatabase setup completed successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
        return False

    return True

if __name__ == "__main__":
    create_user_table()