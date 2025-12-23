import logging
import sys
import os
from pathlib import Path
from datetime import datetime

from backup import run_backup
from gdrive import GoogleDriveClient

# Setup Logging
def setup_logging():
    log_file = "backup.txt"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logging.info("========================================")
    logging.info("   Starting Automation Backup Process   ")
    logging.info("========================================")

    try:
        # 1. Run Backup
        logging.info(">>> STEP 1: Executing pfSense Backup...")
        backup_file = run_backup()
        
        if not backup_file or not backup_file.exists():
            raise RuntimeError("Backup file was not created or found.")
        
        logging.info(f"Backup file verified at: {backup_file}")

        # 2. Upload to Google Drive
        logging.info(">>> STEP 2: Uploading to Google Drive...")
        
        # Initialize client (it will read env vars for auth)
        client = GoogleDriveClient()
        
        # Check if file already exists
        existing_file = client.find_file(backup_file.name)
        
        if existing_file:
            logging.info(f"File '{backup_file.name}' already exists in Google Drive. Skipping upload.")
            res = existing_file
            status_msg = "File already exists (Skipped Upload)"
        else:
            # Upload
            res = client.upload_file(backup_file)
            status_msg = "Upload Successful!"
        
        file_id = res.get('id')
        web_link = res.get('webViewLink') # Some fields might depend on fields requested
        
        logging.info(status_msg)
        logging.info(f"File ID: {file_id}")
        if web_link:
            logging.info(f"Link: {web_link}")
        
        logging.info("========================================")
        logging.info("       Process Completed Successfully   ")
        logging.info("========================================")

    except Exception as e:
        logging.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
