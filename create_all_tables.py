import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_all_tables():
    """Create all database tables using PyMySQL"""

    # Get database connection details from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        return

    # Parse the database URL
    try:
        if db_url.startswith('mysql+pymysql://'):
            db_url = db_url[len('mysql+pymysql://'):]

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

        # Create all tables
        tables_sql = {
            'category': """
                CREATE TABLE IF NOT EXISTS `category` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `name` VARCHAR(100) UNIQUE NOT NULL,
                    `slug` VARCHAR(100) UNIQUE NOT NULL,
                    `description` TEXT,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            'post': """
                CREATE TABLE IF NOT EXISTS `post` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `title` VARCHAR(200) NOT NULL,
                    `slug` VARCHAR(200) UNIQUE NOT NULL,
                    `content` TEXT NOT NULL,
                    `excerpt` TEXT,
                    `featured_image` VARCHAR(300),
                    `author_id` INT NOT NULL,
                    `status` VARCHAR(20) DEFAULT 'published',
                    `meta_title` VARCHAR(200),
                    `meta_description` TEXT,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (`author_id`) REFERENCES `user`(`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            'product': """
                CREATE TABLE IF NOT EXISTS `product` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `name` VARCHAR(200) NOT NULL,
                    `slug` VARCHAR(200) UNIQUE NOT NULL,
                    `description` TEXT NOT NULL,
                    `short_description` TEXT,
                    `price` DECIMAL(10,2) NOT NULL,
                    `sale_price` DECIMAL(10,2),
                    `sku` VARCHAR(100) UNIQUE NOT NULL,
                    `stock_quantity` INT DEFAULT 0,
                    `category_id` INT,
                    `featured_image` VARCHAR(300),
                    `images` JSON,
                    `status` VARCHAR(20) DEFAULT 'active',
                    `meta_title` VARCHAR(200),
                    `meta_description` TEXT,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (`category_id`) REFERENCES `category`(`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            'cart_item': """
                CREATE TABLE IF NOT EXISTS `cart_item` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `user_id` INT NOT NULL,
                    `product_id` INT NOT NULL,
                    `quantity` INT NOT NULL DEFAULT 1,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
                    FOREIGN KEY (`product_id`) REFERENCES `product`(`id`),
                    UNIQUE KEY `unique_user_product` (`user_id`, `product_id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            'order': """
                CREATE TABLE IF NOT EXISTS `order` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `order_number` VARCHAR(50) UNIQUE NOT NULL,
                    `user_id` INT NOT NULL,
                    `total_amount` DECIMAL(10,2) NOT NULL,
                    `status` VARCHAR(20) DEFAULT 'pending',
                    `payment_status` VARCHAR(20) DEFAULT 'pending',
                    `shipping_address` JSON,
                    `billing_address` JSON,
                    `notes` TEXT,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            'order_item': """
                CREATE TABLE IF NOT EXISTS `order_item` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `order_id` INT NOT NULL,
                    `product_id` INT NOT NULL,
                    `quantity` INT NOT NULL,
                    `price` DECIMAL(10,2) NOT NULL,
                    `total` DECIMAL(10,2) NOT NULL,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (`order_id`) REFERENCES `order`(`id`),
                    FOREIGN KEY (`product_id`) REFERENCES `product`(`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            'payment': """
                CREATE TABLE IF NOT EXISTS `payment` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `order_id` INT NOT NULL,
                    `amount` DECIMAL(10,2) NOT NULL,
                    `payment_method` VARCHAR(50) NOT NULL,
                    `transaction_id` VARCHAR(100),
                    `status` VARCHAR(20) DEFAULT 'pending',
                    `payment_data` JSON,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (`order_id`) REFERENCES `order`(`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        }

        # Create each table
        for table_name, sql in tables_sql.items():
            print(f"Creating {table_name} table...")
            cursor.execute(sql)
            print(f"✓ {table_name} table created successfully!")

        # Verify all tables exist
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        expected_tables = ['user', 'category', 'post', 'product', 'cart_item', 'order', 'order_item', 'payment']

        print(f"\nVerifying tables:")
        for table in expected_tables:
            if table in existing_tables:
                print(f"✓ {table} table exists")
            else:
                print(f"✗ {table} table missing")

        print(f"\nTotal tables created: {len([t for t in expected_tables if t in existing_tables])}/{len(expected_tables)}")

        # Close connections
        cursor.close()
        connection.close()
        print("\nDatabase setup completed successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
        return False

    return True

if __name__ == "__main__":
    create_all_tables()