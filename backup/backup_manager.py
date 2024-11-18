from typing import Optional, Dict, List
import os
from datetime import datetime
from pathlib import Path
from logger import DatabaseLogger
from backup.postgres_backup import pg_backup
from storage.local_storage import LocalStorageManager
from storage.cloud_storage import CloudStorageManager
from restore.restore import restore_backup
from notifications.notifier import SlackNotifier
import json
from pathlib import Path

class BackupManager:
    def __init__(self, config: Optional[Dict] = None):
        self.logger = DatabaseLogger()

        if config is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config_path = project_root / "config.json"
            
            if not config_path.exists():
                raise FileNotFoundError(f"config.json not found at {config_path}")
                
            try:
                with open(config_path) as f:
                    config = json.load(f)
                self.logger.info(f"Successfully loaded config from {config_path}")
            except Exception as e:
                raise Exception(f"Failed to load config.json: {str(e)}")

        self.config = config
        self.local_storage = LocalStorageManager(config['local_storage_dir'])
        self.cloud_storage = CloudStorageManager() if config.get('use_cloud') else None
        
        os.makedirs(config['local_storage_dir'], exist_ok=True)
        
        self.backup_functions = {
            'postgres': pg_backup,
        }

        self.notifier = None
        if config.get('notification_enabled', False):
            try:
                self.notifier = SlackNotifier(
                    webhook_url=config.get('slack_webhook'),
                    logger=self.logger
                )
                self.logger.info("Slack notifier initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Slack notifier: {str(e)}")

    def notify(self, operation: str, success: bool, details: Optional[str] = None, error: Optional[str] = None):
        if self.notifier:
            self.notifier.send_notification(operation, success, details, error)


    @DatabaseLogger().log_backup_operation
    def perform_backup(self, db_type: str, compress: bool = False, store_locally: bool = True, 
                      store_in_cloud: bool = False) -> Optional[str]:
        try:
            backup_func = self.backup_functions.get(db_type.lower())
            if not backup_func:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            
            self.logger.log_database_action(
                "backup_start",
                {"db_type": db_type, "compress": compress}
            )
            
            # temp backup
            backup_file = backup_func(self.config['local_storage_dir'], compress)
            if not backup_file:
                raise Exception("Backup failed")
            
            result_path = None
            
            # store
            if store_locally:
                local_path = self.local_storage.save_backup(backup_file)
                self.logger.log_storage_operation("local", "save", local_path, True)
                result_path = local_path

            
            if store_in_cloud and self.cloud_storage:
                cloud_path = self.cloud_storage.upload_backup(backup_file, compress)
                self.logger.log_storage_operation("cloud", "upload", cloud_path, True)
                result_path = cloud_path
            
            if not store_locally and os.path.exists(backup_file):
                os.remove(backup_file)
                
            self.notify(
                "backup",
                True,
                f"Database: {db_type}"
            )
                
            return result_path
            
        except Exception as e:
            self.logger.log_critical_error("Backup operation failed", e)
            self.notify("backup", False, f"Database: {db_type}", str(e))
            return None
    
    def list_backups(self, include_cloud: bool = True) -> List[Dict]:
        backups = []
        
        local_backups = self.local_storage.list_backups()
        for backup in local_backups:
            backup['storage'] = 'local'
            backups.append(backup)
        
        if include_cloud and self.cloud_storage:
            try:
                cloud_backups = self.cloud_storage.list_backups()
                for backup in cloud_backups:
                    backup['storage'] = 'cloud'
                    backups.append(backup)
            except Exception as e:
                print(f"Warning: Failed to list cloud backups: {e}")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def delete_backup(self, backup_name: str, storage_type: str = 'local') -> bool:
        try:
            self.logger.info(f"Attempting to delete backup: {backup_name} from {storage_type} storage")
            if storage_type == 'local':
                result = self.local_storage.delete_backup(backup_name)
                self.logger.info(f"Local delete result: {result}")
                return result
            elif storage_type == 'cloud' and self.cloud_storage:
                result = self.cloud_storage.delete_backup(backup_name)
                self.logger.info(f"Cloud delete result: {result}")
                return result
            else:
                self.logger.error(f"Invalid storage type: {storage_type}")
                return False
        except Exception as e:
            self.logger.error(f"Delete failed: {str(e)}")
            return False
                 
    def restore_backup(self, backup_file: str, db_type: str, target_db: Optional[str] = None, from_cloud: bool = False) -> bool:
        try:
            success = restore_backup(
                backup_file=backup_file,
                target_db=target_db,
                cloud_manager=self.cloud_storage if from_cloud else None,
                is_cloud_backup=from_cloud,
                db_type=db_type.lower()
            )
            storage_type = "cloud" if from_cloud else "local"
            if self.notifier:
                self.notify(
                    "restore",
                    success,
                    f"Database: {db_type}\nSource: {storage_type}\nFile: {backup_file}"
                )        
            return success
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Restore failed: {error_msg}")
            if self.notifier:
                self.notify("restore", False, f"Database: {db_type}", error_msg)
            return False
