import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
from functools import wraps
import traceback
from logging.handlers import RotatingFileHandler

class DatabaseLogger:
    def __init__(self, app_name: str = "DatabaseBackup"):
        self.app_name = app_name
        self.log_file = 'logs/backup.log'
        self.setup_logger()
        
    def setup_logger(self):
        os.makedirs('logs', exist_ok=True)
        
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,
            backupCount=5           
        )
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_backup_operation(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = func.__name__
            self.info(f"Starting {operation_name}")
            try:
                result = func(*args, **kwargs)
                self.info(f"Completed {operation_name} successfully")
                return result
            except Exception as e:
                self.error(f"Failed {operation_name}: {str(e)}")
                self.error(f"Stack trace: {traceback.format_exc()}")
                raise
        return wrapper

    def log_database_action(self, action: str, details: dict):
        self.info(f"Database Action: {action}")
        self.debug(f"Details: {json.dumps(details)}")

    def log_storage_operation(self, storage_type: str, operation: str, file_path: str, success: bool):
        status = "succeeded" if success else "failed"
        self.info(f"{storage_type} storage {operation} {status} for {file_path}")

    def log_critical_error(self, error_msg: str, error: Exception):
        self.logger.critical(f"{error_msg}: {str(error)}")
        self.logger.critical(f"Stack trace: {traceback.format_exc()}")

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)
