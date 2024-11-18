import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        connection = mysql.connector.connect(
            database=os.getenv("MGDB_NAME"),
            user=os.getenv("MGDB_USER"),
            host=os.getenv("MGDB_HOST"),
            password=os.getenv("MGDB_PASSWORD"),
            port=os.getenv("MGDB_PORT")
        )
        print("Connection successful")
        return connection
    except Error as e:
        print(f"Error: {e}")
        
    
get_connection()