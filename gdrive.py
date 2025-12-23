from __future__ import annotations
import os
from pathlib import Path
import mimetypes
from typing import Optional, Dict, Any

from dotenv import load_dotenv

import google.auth.exceptions
import googleapiclient.errors
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


load_dotenv()


class GoogleDriveClient:
    def __init__(self, scopes: Optional[list] = None):
        """Create a Drive API client using Client ID, Secret and Refresh Token.

        Args:
            scopes: list of OAuth scopes to request (defaults to full Drive scope).
        """
        # Try OAuth2 (Client ID + Secret + Refresh Token)
        client_id = os.getenv("GDRIVE_CLIENT_ID")
        client_secret = os.getenv("GDRIVE_CLIENT_SECRET")
        refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN")

        if not (client_id and client_secret and refresh_token):
            raise RuntimeError(
                "Authentication missing. Set GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, and GDRIVE_REFRESH_TOKEN."
            )

        from google.oauth2.credentials import Credentials
        creds = Credentials(
            None, # Access token (will be refreshed)
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        
        self.scopes = scopes or ["https://www.googleapis.com/auth/drive"]
        self.service = build("drive", "v3", credentials=creds)

    def find_file(self, name: str, folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check if a file with `name` exists in `folder_id`."""
        folder = folder_id or os.getenv("GDRIVE_FOLDER_ID")
        if not folder:
            raise RuntimeError("No destination folder specified.")

        query = f"name = '{name}' and '{folder}' in parents and trashed = false"

        try:
            results = self.service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name, webViewLink)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1
            ).execute()
            files = results.get('files', [])
            return files[0] if files else None
        except Exception as e:
            raise RuntimeError(f"Error searching for file: {e}")

    def upload_file(self, local_path: str | Path, folder_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload a file to Google Drive inside `folder_id` (or env `GDRIVE_FOLDER_ID`).

        Returns the file resource returned by the Drive API.
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(local_path)

        folder = folder_id or os.getenv("GDRIVE_FOLDER_ID")
        if not folder:
            raise RuntimeError("No destination folder specified. Set GDRIVE_FOLDER_ID or pass folder_id argument.")

        mime_type = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
        file_metadata = {"name": local_path.name, "parents": [folder]}
        if metadata:
            file_metadata.update(metadata)

        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

        try:
            created = self.service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields="id,name,mimeType,parents,webViewLink", 
                supportsAllDrives=True
            ).execute()
        except google.auth.exceptions.RefreshError as e:
            raise RuntimeError(f"Authentication failed (RefreshError): {e}. CHECK YOUR .ENV CREDENTIALS (Client ID/Secret).") from e
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 404:
                raise RuntimeError(
                    f"Google Drive Folder ID not found or not accessible: '{folder}'. "
                    "Make sure the ID is correct and the authenticated user has access to it."
                ) from e
            raise
            
        return created


if __name__ == "__main__":
    # simple CLI example
    import argparse

    p = argparse.ArgumentParser(description="Upload a file to Google Drive folder from env or arg")
    p.add_argument("file", help="Local path to file to upload")
    p.add_argument("--folder", help="Drive folder id (optional, overrides env)")
    args = p.parse_args()

    client = GoogleDriveClient()
    res = client.upload_file(args.file, folder_id=args.folder)
    print("Uploaded:", res)
