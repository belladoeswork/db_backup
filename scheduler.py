import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
from dotenv import load_dotenv
from backup.backup_manager import BackupManager
from logger import DatabaseLogger
from notifications.notifier import SlackNotifier

class BackupScheduler:
    def __init__(self, config_path: Optional[str] = None):
        load_dotenv()
        
        self.logger = DatabaseLogger()
        self.config = self.load_config(config_path)
        self.backup_manager = BackupManager(self.config)
        
        self.notifier = None
        if self.config.get('notification_enabled'):
            try:
                self.notifier = SlackNotifier(
                    webhook_url=self.config.get('slack_webhook'),
                    logger=self.logger
                )
                self.logger.info("Slack notifier initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Slack notifier: {str(e)}")

    def load_config(self, config_path: Optional[str] = None) -> dict:
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.logger.info(f"Successfully loaded config from {config_path}")
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            raise

        # Override with environment variables if they exist
        env_mappings = {
            'SUPABASE_NAME': ('db_name', str),
            'SUPABASE_USER': ('db_user', str),
            'SUPABASE_HOST': ('db_host', str),
            'SUPABASE_PASSWORD': ('db_password', str),
            'SUPABASE_PORT': ('db_port', int),
            'GOOGLE_PROJECT_ID': ('cloud_storage.project_id', str),
            'GOOGLE_REGION': ('cloud_storage.region', str)
        }

        for env_var, (config_path, type_cast) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                keys = config_path.split('.')
                current = config
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[keys[-1]] = type_cast(value)

        # always save on cloud
        config['store_in_cloud'] = True
        config['use_cloud'] = True
        
        required_fields = ['cloud_storage.bucket', 'cloud_storage.project_id', 'cloud_storage.region']
        for field in required_fields:
            keys = field.split('.')
            current = config
            for key in keys:
                if key not in current:
                    raise ValueError(f"Missing required configuration: {field}")
                current = current[key]

        return config

    def run_backup(self) -> bool:
        """Execute the backup process"""
        try:
            self.logger.info("Starting scheduled backup...")
            
            result = self.backup_manager.perform_backup(
                db_type=self.config['db_type'],
                compress=self.config['compress'],
                store_locally=False,
                store_in_cloud=True
            )
            
            if result:
                success_msg = f"Backup completed successfully: {result}"
                self.logger.info(success_msg)
                if self.notifier:
                    self.notifier.send_notification(
                        operation="backup",
                        status=True,
                        details=f"Backup saved to cloud storage: {result}"
                    )
                return True
            else:
                error_msg = "Backup failed: No result returned"
                self.logger.error(error_msg)
                if self.notifier:
                    self.notifier.send_notification(
                        operation="backup",
                        status=False,
                        error=error_msg
                    )
                return False
                
        except Exception as e:
            error_msg = f"Backup failed with error: {str(e)}"
            self.logger.error(error_msg)
            if self.notifier:
                self.notifier.send_notification(
                    operation="backup",
                    status=False,
                    error=error_msg
                )
            return False

def main():
    """Main entry point for the scheduler"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    scheduler = BackupScheduler(config_path)
    scheduler.run_backup()

if __name__ == "__main__":
    main()
