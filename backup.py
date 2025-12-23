import time
import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import logging

def run_backup() -> Path:
    logging.info("Starting backup process...")
    # prepare local download directory (project/files)
    download_dir = Path(__file__).resolve().parent / "files"
    download_dir.mkdir(parents=True, exist_ok=True)

    # load environment variables from .env (see .env.example)
    load_dotenv()
    PFSENSE_USER = os.getenv("PFSENSE_USER")
    PFSENSE_PASS = os.getenv("PFSENSE_PASS")
    if not PFSENSE_USER or not PFSENSE_PASS:
        raise RuntimeError(
            "PFSENSE_USER and PFSENSE_PASS must be set in a .env file. Copy .env.example -> .env and fill values."
        )

    options = Options()
    # Chrome preferences to auto-download to `files` and disable prompt/warning
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "profile.default_content_settings.popups": 0,
        # Disable Chrome's download protection that shows "This file can't be scanned"
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
    }
    options.add_argument("--headless=new")
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--ignore-ssl-errors=yes")
    
    # Headless mode options if needed in future (optional)
    # options.add_argument("--headless=new")

    logging.info("Initializing WebDriver...")
    driver = webdriver.Chrome(options=options)
    # Initialize WebDriverWait
    wait = WebDriverWait(driver, 20)

    try:
        target_url = os.getenv("TARGET_URL", "https://localhost")
        logging.info(f"Navigating to {target_url}...")
        driver.get(target_url)
        assert "pfSense - Login" in driver.title, "Failed to load pfSense login page"
        
        logging.info("Logging in...")
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[2]/div/form/input[2]'))).send_keys(PFSENSE_USER)
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[2]/div/form/input[3]'))).send_keys(PFSENSE_PASS)
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[2]/div/form/input[4]'))).click()
        
        # Wait for login to complete (title should change)
        wait.until(lambda d: "pfSense - Login" not in d.title)

        logging.info("Navigating to Backup section...")        
        driver.get(f'{target_url}/diag_backup.php')        

        # Wait for the Download button to be clickable
        downloadButton = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/div[1]/div[2]/div[8]/div/button')))

        before = set(p.name for p in download_dir.iterdir())
        logging.info("Clicking download button...")
        downloadButton.click()
        timeout = 60
        poll = 0.5
        end = time.time() + timeout
        downloaded_path = None
        
        logging.info("Waiting for download to complete...")
        while time.time() < end:
            now_files = [p for p in download_dir.iterdir() if p.name not in before]
            done_files = [p for p in now_files if not p.name.endswith('.crdownload') and not p.name.endswith('.tmp')]
            if done_files:
                downloaded_path = max(done_files, key=lambda p: p.stat().st_mtime)
                # Small wait to ensure file handle is released by Chrome
                time.sleep(2.0)
                break
            time.sleep(poll)

        if not downloaded_path:
            raise RuntimeError("Download did not complete within timeout")

        from datetime import date
        today = date.today()
        suffix = downloaded_path.suffix
        # Filename Format: PREFIX - BKP_DD.MM.AAAA.xml
        prefix = os.getenv("BACKUP_FILENAME_PREFIX", "spfSense")
        target_name = f"{prefix}{today.day:02d}.{today.month:02d}.{today.year}{suffix}"
        target_path = download_dir / target_name

        def sha256_of(path: Path) -> str:
            h = hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            return h.hexdigest()

        def safe_rename(src: Path, dst: Path, retries=5, delay=1.0):
            for i in range(retries):
                try:
                    os.replace(str(src), str(dst))
                    return
                except PermissionError:
                    if i == retries - 1:
                        raise
                    time.sleep(delay)
                except Exception:
                    src.replace(dst)
                    return

        # Process file
        final_path = target_path
        
        if target_path.exists():
            try:
                existing_hash = sha256_of(target_path)
                new_hash = sha256_of(downloaded_path)
            except Exception as e:
                logging.warning(f"Error calculating hash: {e}")
                # fallback: compare file size
                if target_path.stat().st_size == downloaded_path.stat().st_size:
                    existing_hash = new_hash = None
                else:
                    existing_hash = 'DIFFER'
                    new_hash = 'DIFFER'

            if existing_hash is None or existing_hash == new_hash:
                try:
                    downloaded_path.unlink()
                except Exception:
                    pass
                logging.info(f"Existing backup already present: {target_path} (skipped creating duplicate)")
            else:
                try:
                    safe_rename(downloaded_path, target_path)
                except Exception as e:
                    logging.error(f"Failed to replace file: {e}")
                    raise
                logging.info(f"Replaced existing backup with new download: {target_path}")
        else:
            try:
                safe_rename(downloaded_path, target_path)
            except Exception as e:
                logging.error(f"Failed to save file: {e}")
                raise
            logging.info(f"Saved backup as: {target_path}")
            
        return final_path

    finally:
        logging.info("Closing WebDriver...")
        driver.quit()

if __name__ == "__main__":
    # Basic logging setup for standalone run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        run_backup()
    except Exception as e:
        logging.error(f"Backup failed: {e}")



