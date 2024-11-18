import os
import subprocess
import shutil
from typing import Optional, Tuple
from tempfile import TemporaryDirectory
from connectors.postgres_connector import get_connection
from logger import DatabaseLogger


def check_postgres_tools() -> Tuple[bool, str]:
    tools = ['pg_restore']
    missing = []
    
    for tool in tools:
        if not shutil.which(tool):
            missing.append(tool)
    
    if missing:
        install_instructions = """
PostgreSQL command line tools are not found. Please install them:

For MacOS:
    brew install postgresql

For Ubuntu/Debian:
    sudo apt-get install postgresql-client

For Windows:
    1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
    2. During installation, ensure "Command Line Tools" is selected
    3. Add the PostgreSQL bin directory to your system PATH
"""
        return False, f"Missing required PostgreSQL tools: {', '.join(missing)}\n{install_instructions}"
    
    return True, ""

def postgres_restore(backup_file: str, target_db: Optional[str] = None) -> bool:
    try:
        tools_available, error_message = check_postgres_tools()
        if not tools_available:
            raise Exception(error_message)
        
        connection = get_connection()
        if not connection:
            raise Exception("Unable to connect to the database")
        
        try:
            params = connection.get_dsn_parameters()
            db_name = target_db or params["dbname"]
            host = params.get("host")
            port = params.get("port")
            user = params.get("user")
            pwd = os.getenv("SUPABASE_PASSWORD")

            if not all([db_name, host, port, user, pwd]):
                raise Exception("Incomplete database connection parameters")

            command = [
                "pg_restore",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                "--no-comments",
                "--verbose",
                "--schema=public",
                "--exclude-schema=auth",
                "--exclude-schema=storage",
                "--exclude-schema=graphql",
                "--exclude-schema=realtime",
                "--exclude-schema=vault",
                "--exclude-schema=extensions",
                "--disable-triggers",
                f"--dbname=postgresql://{user}:{pwd}@{host}:{port}/{db_name}",
                str(backup_file)
            ]
            
            print(f"\nRestoring backup to database: {db_name}")
            print("This may take a while...")
            
            env = os.environ.copy()
            env["PGSSLMODE"] = "require"
            env["PGGSSENCMODE"] = "disable"
            
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("Warnings during restore (these are usually okay for Supabase):")
                print(result.stderr)
                
            print("\nRestore completed!")
            if result.stdout:
                print("Details:", result.stdout)
                
            return True
            
        finally:
            connection.close()
                
    except Exception as e:
        print(f"Error during restore: {str(e)}")
        return False

RESTORE_FUNCTIONS = {
    'postgres': postgres_restore
}
    
def restore_backup(backup_file: str, target_db: Optional[str] = None, 
                  cloud_manager=None, is_cloud_backup: bool = False, 
                  db_type: str = 'postgres') -> bool:
    logger = DatabaseLogger()    
    temp_dir = None
    try:
        logger.log_database_action(
            "restore_start",
            {
                "file": backup_file,
                "target_db": target_db,
                "db_type": db_type,
                "is_cloud": is_cloud_backup
            }
        )        
             
        restore_func = RESTORE_FUNCTIONS.get(db_type.lower())
        if not restore_func:
            raise ValueError(f"Unsupported database type: {db_type}")

        local_backup = backup_file
        if is_cloud_backup and cloud_manager:
            from tempfile import mkdtemp
            temp_dir = mkdtemp()
            logger.info(f"Created temporary directory: {temp_dir}")
            local_backup = cloud_manager.download_backup(backup_file, temp_dir)
            logger.log_storage_operation("cloud", "download", local_backup, True)

        if not os.path.exists(local_backup):
            raise Exception(f"Backup file not found: {local_backup}")
            
        success = restore_func(local_backup, target_db)
        logger.log_database_action(
            "restore_complete",
            {"success": success}
        )
        return success

    except Exception as e:
        logger.log_critical_error("Restore operation failed", e)
        return False
        
    finally:
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

