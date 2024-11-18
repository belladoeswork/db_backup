# Database Backup Utility

A command-line utility for managing database backups with support for both local and cloud storage. Currently supports PostgreSQL databases, with extensible architecture for future database support.

## Features

- **Database Support**
  - PostgreSQL (current)
  - Extensible architecture for future database types (MySQL, MongoDB, etc.)

- **Storage Options**
  - Local filesystem storage
  - Google Cloud Storage integration
  - Compressed backup support

- **Notifications**
  - Slack integration for backup/restore notifications
  - Detailed logging system

- **Operations**
  - Backup creation (local/cloud)
  - Backup restoration
  - Backup deletion
  - Backup listing
  - Scheduled backups

## Prerequisites

- Google Cloud account (with billing)
- Database account and connection credentials

### Installing PostgreSQL Tools

#### macOS
```bash
brew install postgresql@15
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backup-utility
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
touch .env.local
```

Edit `.env.local` with your database credentials:
```
SUPABASE_NAME=your_database
SUPABASE_USER=your_username
SUPABASE_HOST=your_host
SUPABASE_PASSWORD=your_password
SUPABASE_PORT=database_port
```

5. Configure the application:
```bash
touch config.json
```

Edit `config.json` with your settings:
```json
{
    "local_storage_dir": "/path/to/backup/directory",
    "use_cloud": true,
    "compress": true,
    "db_type": "postgres",
    "store_locally": true,
    "store_in_cloud": true,
    "notification_enabled": true,
    "slack_webhook": "your_slack_webhook_url",
    "cloud_storage": {
        "type": "gcs",
        "bucket": "your_bucket_name",
        "region": "your_region",
        "project_id": "your_project_id"
    }
}
```

## Usage

### Creating Backups

#### Local Backup
```bash
python main.py backup --db postgres
```

#### Cloud Backup
```bash
python main.py backup --db postgres --cloud
```

#### Compressed Backup
```bash
python main.py backup --db postgres --compress
```

### Listing Backups

#### List Local Backups
```bash
python main.py restore --list
```

#### List Cloud Backups
```bash
python main.py restore --list --cloud
```

### Restoring Backups

#### Restore from Local
```bash
python main.py restore --file backup_filename.dump
```

#### Restore from Cloud
```bash
python main.py restore --file backup_filename.dump --cloud
```

#### Restore to Different Database
```bash
python main.py restore --file backup_filename.dump --target-db new_database_name
```

### Deleting Backups

#### Delete Local Backup
```bash
python main.py delete --file backup_filename.dump
```

#### Delete Cloud Backup
```bash
python main.py delete --file backup_filename.dump --cloud
```

### Scheduling Backups (Cron Job)

1. Make the scheduler executable:
```bash
chmod +x scheduler.py
```

2. Add to crontab (example for daily backup at 2 AM):
```bash
crontab -e
```

Add the line:
```
0 2 * * * cd /path/to/backup-utility && /path/to/venv/bin/python scheduler.py
```

## Logging

Logs are stored in the `logs/backup.log` file. The logging system uses rotation to maintain file sizes, keeping the last 5 log files with a maximum size of 10MB each.

## Cloud Storage Setup

1. Install Google Cloud SDK
2. Authenticate with Google Cloud:
```bash
gcloud auth application-default login
```

3. Set your project:
```bash
gcloud config set project your-project-id
```

4. Ensure your service account has the necessary permissions for Google Cloud Storage operations.