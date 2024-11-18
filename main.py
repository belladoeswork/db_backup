import os
import argparse
from pathlib import Path
from backup.backup_manager import BackupManager
import json

def get_db_type_from_filename(filename: str) -> str:
    filename = os.path.basename(filename).lower()
    
    if 'postgres' in filename or 'supabase' in filename:
        return 'postgres'
    elif 'mysql' in filename:
        return 'mysql'
    elif 'mongo' in filename:
        return 'mongodb'
    else:
        raise ValueError(f"Could not determine database type from filename: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Database Backup CLI")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    backup_parser = subparsers.add_parser('backup', help='Perform a database backup')
    backup_parser.add_argument('--db', type=str, required=True, choices=['postgres'], help='Database type (postgres)')
    backup_parser.add_argument('--compress', action='store_true', help='Compress backup')
    backup_parser.add_argument('--cloud', action='store_true', help='Store in cloud')
    backup_parser.add_argument('--no-local', action='store_true', help='Skip local storage')
    
    restore_parser = subparsers.add_parser('restore', help='Restore a database backup')
    restore_group = restore_parser.add_mutually_exclusive_group(required=True)
    restore_group.add_argument('--list', action='store_true', help='List available backups')
    restore_group.add_argument('--file', type=str, help='Specific backup file to restore')
    restore_parser.add_argument('--db', type=str, choices=['postgres'], 
                              help='Optional: Override database type detection')
    restore_parser.add_argument('--target-db', type=str, help='Target database name (optional)')
    restore_parser.add_argument('--cloud', action='store_true', help='List/restore from cloud storage')
    
    delete_parser = subparsers.add_parser('delete', help='Delete a backup')
    delete_parser.add_argument('--file', type=str, required=True, help='Backup file to delete')
    delete_parser.add_argument('--cloud', action='store_true', help='Delete from cloud storage')
    
    args = parser.parse_args()
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
    backup_manager = BackupManager(config)
    
    if args.command == 'backup':
        store_locally = not args.cloud
        store_in_cloud = args.cloud
        
        result = backup_manager.perform_backup(
            db_type=args.db,
            compress=args.compress,
            store_locally=store_locally,
            store_in_cloud=store_in_cloud
        )
        if result:
            if store_in_cloud:
                print(f"Backup uploaded to cloud storage: {result}")
            else:
                print(f"Backup saved locally: {result}")
        else:
            print("Backup failed")
    
    elif args.command == 'restore':
        if args.list:
            backups = backup_manager.list_backups(include_cloud=args.cloud)
            if not backups:
                print("No backups found")
                return
                
            print("\nAvailable backups:")
            for i, backup in enumerate(backups, 1):
                storage_type = backup['storage']
                print(f"{i}. [{storage_type}] {backup['name']} "
                      f"({backup['size_mb']}MB) - Created: {backup['created']}")
            
            if not args.file:
                while True:
                    try:
                        choice = int(input("\nEnter the number of the backup to restore (0 to cancel): "))
                        if choice == 0:
                            return
                        if 1 <= choice <= len(backups):
                            selected_backup = backups[choice - 1]
                            backup_name = selected_backup['name']
                            
                            try:
                                db_type = args.db or get_db_type_from_filename(backup_name)
                                
                                success = backup_manager.restore_backup(
                                    selected_backup['path'] if 'path' in selected_backup else backup_name,
                                    db_type,
                                    args.target_db,
                                    from_cloud=(selected_backup['storage'] == 'cloud')
                                )
                                if success:
                                    print("Restore completed successfully")
                                else:
                                    print("Restore failed")
                            except ValueError as e:
                                print(f"Error: {str(e)}")
                                print("Please specify database type using --db option")
                            break
                        print("Invalid choice. Please try again.")
                    except ValueError:
                        print("Please enter a valid number.")
        
        elif args.file:
            try:
                db_type = args.db or get_db_type_from_filename(args.file)
                
                if not args.cloud:
                    backup_file = Path(args.file)
                    if not backup_file.exists():
                        print(f"Backup file not found: {args.file}")
                        return
                    
                success = backup_manager.restore_backup(
                    args.file,
                    db_type,
                    args.target_db,
                    from_cloud=args.cloud
                )
                if success:
                    print("Restore completed successfully")
                else:
                    print("Restore failed")
            except ValueError as e:
                print(f"Error: {str(e)}")
                print("Please specify database type using --db option")
        
        else:
            parser.print_help()
    
    elif args.command == 'delete':
        success = backup_manager.delete_backup(
            args.file,
            'cloud' if args.cloud else 'local'
        )
        if success:
            print(f"Backup deleted successfully: {args.file}")
        else:
            print("Delete failed")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
