#!/usr/bin/env python3
"""
Script to clear Users table at startup - maintains all other data
"""
import os
import sys
import time
import mysql.connector
from mysql.connector import Error

def wait_for_db():
    """Wait for database to be available"""
    max_retries = 30
    for i in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host=os.getenv('MYSQL_SERVER', 'mariadb'),
                database=os.getenv('MYSQL_DATABASE', 'moviemania'),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', 'rootpassword')
            )
            if connection.is_connected():
                connection.close()
                print("Database is ready!")
                return True
        except Error as e:
            print(f"Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    
    print("Failed to connect to database after retries")
    return False

def clear_users_tables():
    """Clear users-related tables while preserving other data"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_SERVER', 'mariadb'),
            database=os.getenv('MYSQL_DATABASE', 'moviemania'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'rootpassword')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Clear users-related tables in proper order (foreign keys)
            print("Clearing UserGenre table...")
            cursor.execute("DELETE FROM UserGenre;")
            
            print("Clearing MovieUsers table...")
            cursor.execute("DELETE FROM MovieUsers;")
            
            print("Clearing Users table...")
            cursor.execute("DELETE FROM Users;")
            
            # Reset auto increment to start from 1
            cursor.execute("ALTER TABLE Users AUTO_INCREMENT = 1;")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("✅ Users tables cleared successfully!")
            return True
            
    except Error as e:
        print(f"❌ Error clearing users tables: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Waiting for database to be ready...")
    if wait_for_db():
        print("🧹 Clearing users tables...")
        if clear_users_tables():
            print("✅ Startup cleanup completed!")
            sys.exit(0)
        else:
            print("❌ Startup cleanup failed!")
            sys.exit(1)
    else:
        print("❌ Database not available!")
        sys.exit(1)