import os
import shutil
from datetime import datetime
from pathlib import Path

class LocalStorageManager():
    def __init__(self, storage_dir):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_backup(self, backup_file):
        try:
            backup_path = self.storage_dir / os.path.basename(backup_file)
            if os.path.abspath(backup_file) != os.path.abspath(backup_path):
                shutil.copy2(backup_file, backup_path)
                os.remove(backup_file)

                temp_dir = os.path.dirname(backup_file)
                if not os.listdir(temp_dir) and 'pg_backup_' in temp_dir:
                    os.rmdir(temp_dir)
                    
            print(f"Backup saved locally: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"Error saving backup locally: {str(e)}")
            return None

    def list_backups(self):
        try:
            backups = []
            for file in self.storage_dir.glob("supabase_backup_*.dump"):
                stats = file.stat()
                backups.append({
                    'name': file.name,
                    'path': str(file),
                    'size_mb': round(stats.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            return sorted(backups, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            print(f"Error listing local backups: {str(e)}")
            return []

    def get_backup(self, backup_name, local_path):
        try:
            source = self.storage_dir / backup_name
            if not source.exists():
                print(f"Backup file not found: {backup_name}")
                return None
            
            dest = Path(local_path) / backup_name
            shutil.copy2(source, dest)
            return str(dest)
        except Exception as e:
            print(f"Error retrieving backup: {str(e)}")
            return None

    def delete_backup(self, backup_name):
        try:
            backup_path = self.storage_dir / backup_name
            if backup_path.exists():
                backup_path.unlink()
                print(f"Deleted local backup: {backup_name}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting backup: {str(e)}")
            return False

