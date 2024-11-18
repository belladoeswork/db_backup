from google.cloud import storage
from datetime import datetime
import gzip
import shutil
from pathlib import Path


class CloudStorageManager:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.get_bucket('dbbucket1234')

    def compress_file(self, file_path: Path) -> Path:
        compressed_file = file_path.with_suffix(file_path.suffix + '.gz')
        with file_path.open('rb') as f_in:
            with gzip.open(str(compressed_file), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return compressed_file

    def upload_backup(self, file_path: str, compress: bool = True) -> str:
        try:
            file_path = Path(file_path)
            filename = file_path.name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cloud_path = f"backups/{timestamp}_{filename}"
            
            if compress:
                upload_path = self.compress_file(file_path)
                cloud_path += '.gz'
            else:
                upload_path = file_path

            blob = self.bucket.blob(cloud_path)
            blob.upload_from_filename(str(upload_path))

            metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'original_name': filename,
                'size': str(upload_path.stat().st_size)
            }
            blob.metadata = metadata
            blob.patch()

            print(f"Backup uploaded to cloud storage: {cloud_path}")
            
            if compress and upload_path != file_path:
                upload_path.unlink()

            return cloud_path

        except Exception as e:
            print(f"Error uploading to cloud storage: {str(e)}")
            return None

    def download_backup(self, cloud_path: str, local_dir: str) -> str:
        try:
            if not cloud_path.startswith('backups/'):
                cloud_path = f'backups/{cloud_path}'
                
            local_dir = Path(local_dir)
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / Path(cloud_path).name
            
            print(f"Downloading {cloud_path} to {local_path}...")
            
            blob = self.bucket.blob(cloud_path)
            if not blob.exists():
                raise Exception(f"Backup file not found in cloud storage: {cloud_path}")
                
            blob.download_to_filename(str(local_path))
            
            if cloud_path.endswith('.gz'):
                decompressed_path = local_path.with_suffix('')
                print(f"Decompressing to {decompressed_path}...")
                with gzip.open(local_path, 'rb') as f_in:
                    with decompressed_path.open('wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                local_path.unlink()
                return str(decompressed_path)
            
            return str(local_path)

        except Exception as e:
            print(f"Error downloading from cloud storage: {str(e)}")
            raise

    def delete_backup(self, cloud_path: str) -> bool:
        try:
            blob = self.bucket.blob(cloud_path)
            blob.delete()
            print(f"Deleted backup: {cloud_path}")
            return True
        except Exception as e:
            print(f"Error deleting cloud backup: {str(e)}")
            return False

    def list_backups(self) -> list:
        try:
            print("Listing cloud backups...")
            blobs = list(self.bucket.list_blobs(prefix='backups/'))
            
            if not blobs:
                print("No cloud backups found")
                return []
                
            backups = []
            for blob in blobs:
                if blob.name.endswith('.dump') or blob.name.endswith('.dump.gz'):
                    size_mb = blob.size / (1024 * 1024)
                    backup_info = {
                        'name': Path(blob.name).name,
                        'path': blob.name,
                        'size_mb': round(size_mb, 2),
                        'created': blob.time_created.strftime('%Y-%m-%d %H:%M:%S'),
                        'metadata': blob.metadata or {}
                    }
                    backups.append(backup_info)
                    print(f"Found cloud backup: {blob.name}")
            
            return backups

        except Exception as e:
            print(f"Error listing cloud backups: {str(e)}")
            raise
        
