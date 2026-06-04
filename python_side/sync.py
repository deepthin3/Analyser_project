#sync.py
#Standalone tool to download source files from IBM i IFS to local directory
#Uses SFTP to download files from the IFS to the local directory
#
# HOW TO RUN:
#   python sync.py
#
# This downloads ALL source files from your configured IFS_PATH to LOCAL_PATH
# Run this once initially, then re-run whenever you need fresh sources from IBM i
import os
import paramiko
from pathlib import Path
from dotenv import load_dotenv
 

load_dotenv()

#This function downloads source files from the IFS to the local directory   
def sync_sources():
    # Validate environment variables first
    host = os.getenv("IBMI_HOST")
    username = os.getenv("IBMI_USER")
    password = os.getenv("IBMI_PASS")
    ifs_path = os.getenv("IFS_PATH")
    local_path = os.getenv("LOCAL_PATH")
    
    # Check that required environment variables are set
    missing = []
    if not host:
        missing.append("IBMI_HOST")
    if not username:
        missing.append("IBMI_USER")
    if not password:
        missing.append("IBMI_PASS")
    if not ifs_path:
        missing.append("IFS_PATH")
    if not local_path:
        missing.append("LOCAL_PATH")
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Check your .env file and try again.")
        return False
    
    sftp = None
    ssh = None
    load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
    print("Looking for .env file in:", Path(__file__).parent.parent / '.env'    )
    print(f"Environment variables loaded: {host}, {username}, {ifs_path}, {local_path}")
    print(f"Syncing sources from {host}:{ifs_path} to {local_path}")
    
    # Create local directory if it doesn't exist
    try:
        os.makedirs(local_path, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Could not create local directory {local_path}: {str(e)}")
        return False

    # Delete files already in local folder 
    try:
        for filename in os.listdir(local_path):
            file_path = os.path.join(local_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Cleared local directory: {local_path}")
    except OSError as e:
        print(f"ERROR: Could not clear local directory: {str(e)}")
        return False

    # Create SSH client object and connect to the IBM i server   
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password, port=2222, timeout=30)
        sftp = ssh.open_sftp()
        #List files in the IFS directory and download them to the local directory
        # List all files in the IFS folder on IBM i
        files = sftp.listdir(ifs_path)
 
        # Filter to only .txt files (our extracted sources)
        # List comprehension: [item for item in list if condition]
        txt_files = [f for f in files if f.endswith('.txt')]
        
        if not txt_files:
            print(f"WARNING: No .txt files found in {ifs_path} on IBM i")
            return False
            
        print(f'Found {len(txt_files)} source files to download...')

        downloaded = 0
        failed_files = []

        for filename in txt_files:
            remote_file = f'{ifs_path}/{filename}'
            local_file = os.path.join(local_path, filename)
            try:
                print(f"Downloading {remote_file} to {local_file}")
                sftp.get(remote_file, local_file)
                downloaded += 1
            except IOError as e:
                print(f"  WARNING: Failed to download {filename}: {str(e)}")
                failed_files.append(filename)
            
            if downloaded % 10 == 0:
                print(f"Downloaded {downloaded} files so far...")   
        
        if failed_files:
            print(f"WARNING: {len(failed_files)} files failed to download: {failed_files}")
            
        print(f"Sync complete. Downloaded {downloaded} files to {local_path}.")
        return downloaded > 0
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")  
        return False
    except Exception as e:
        print(f"Error occurred: {e}")
        return False
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass
         

if __name__ == "__main__":
    sync_sources()