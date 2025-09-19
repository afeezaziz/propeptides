#!/usr/bin/env python3
"""
Test MySQL database connection for blog posts
"""

import pymysql
from datetime import datetime

def test_connection():
    """Test MySQL database connection"""

    db_config = {
        'host': '104.248.150.75',
        'port': 33004,
        'user': 'mariadb',
        'password': '0cZ0FRFBB1UPsmnTKjGfm8iofaBkb0s7JZAggtz1f3RGnqqnu7d2h6dk6zF8EGbv',
        'database': 'default',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    try:
        print("🔌 Connecting to MySQL database...")
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        print("✅ Database connection successful!")

        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"📊 Basic query test: {result}")

        # Check if tables exist
        cursor.execute("""
            SELECT TABLE_NAME, TABLE_COMMENT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'default'
        """)
        tables = cursor.fetchall()

        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  • {table['TABLE_NAME']}: {table['TABLE_COMMENT']}")

        # Check post table specifically
        cursor.execute("""
            SELECT COUNT(*) as count FROM post
        """)
        post_count = cursor.fetchone()['count']
        print(f"\n📝 Current post count: {post_count}")

        if post_count > 0:
            cursor.execute("""
                SELECT title, slug, created_at
                FROM post
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_posts = cursor.fetchall()
            print("\n📋 Recent posts:")
            for post in recent_posts:
                print(f"  • {post['title']}")
                print(f"    Slug: {post['slug']}")
                print(f"    Created: {post['created_at']}")

        return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Database connection closed.")

if __name__ == "__main__":
    test_connection()