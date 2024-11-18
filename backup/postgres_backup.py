import os
import subprocess
import tempfile
from datetime import datetime
from connectors.postgres_connector import get_connection

def pg_backup(output_dir: str, compress: bool = False) -> str:
    connection = get_connection()
    
    if not connection:
        raise Exception("Unable to connect to the PostgreSQL database")
    
    
    temp_dir = tempfile.mkdtemp(prefix="pg_backup_")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        params = connection.get_dsn_parameters()
        db_name = params["dbname"]
        host = params.get("host")
        port = params.get("port")
        user = params.get("user")
        pwd = os.getenv("SUPABASE_PASSWORD")

        if not all([db_name, host, port, user, pwd]):
            raise Exception("Incomplete database connection parameters")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(temp_dir, f"supabase_backup_{db_name}_{timestamp}.dump")

        
        command = [
            "pg_dump",
            f"postgresql://{user}:{pwd}@{host}:{port}/{db_name}",
            "--format=custom",
            f"--file={backup_file}",
            "--verbose",
            "--no-owner",
            "--no-privileges"
        ]
        
        if compress:
            command.append("--compress=9")
        
        env = os.environ.copy()
        env["PGSSLMODE"] = "require"
        env["PGGSSENCMODE"] = "disable"
        env["PGSSLCERT"] = ""
        env["PGSSLKEY"] = ""
        env["PGSSLROOTCERT"] = ""
        
        result = subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stderr:
            print(f"Backup warnings: {result.stderr}")
            
        return backup_file

    except subprocess.CalledProcessError as e:
        raise Exception(f"Backup failed: {e.stderr}")
    
    finally:
        connection.close()
