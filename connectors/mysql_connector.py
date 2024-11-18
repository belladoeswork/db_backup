import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        connection = mysql.connector.connect(
            database=os.getenv("MYSQL_NAME"),
            user=os.getenv("MYSQL_USER"),
            host=os.getenv("MYSQL_HOST"),
            password=os.getenv("MYSQL_PASSWORD"),
            port=os.getenv("MYSQL_PORT")
        )
        print("Connection successful")
        return connection
    except Error as e:
        print(f"Error: {e}")
        
    
get_connection()