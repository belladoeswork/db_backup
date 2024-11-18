import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local')

def get_connection():
    try:
        connection = psycopg2.connect(
            database=os.getenv("SUPABASE_NAME"),
            user=os.getenv("SUPABASE_USER"),
            host=os.getenv("SUPABASE_HOST"),
            password=os.getenv("SUPABASE_PASSWORD"),
            port=os.getenv("SUPABASE_PORT")
        )
        print("Connection successful")
        return connection
    except Error as e:
        print(f"Error: {e}")
        
