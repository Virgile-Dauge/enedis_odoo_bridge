import os
import zipfile

from dotenv import load_dotenv
from pathlib import Path

from datetime import date, datetime
from calendar import monthrange

from Crypto.Cipher import AES
from typing import Callable

import pandas as pd
from pandas import Timestamp
import paramiko
import logging
from typing import Callable

import tempfile

logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
_logger = logging.getLogger('enedis_odoo_bridge')

class CustomLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f'{self.extra["prefix"]}{msg}', kwargs

def get_consumption_names() -> list[str]:
    """
    Retourne une liste des noms de consommation utilisés dans le système.

    Returns:
        list[str]: Liste des noms de consommation.
    """
    return ['HPH', 'HPB', 'HCH', 'HCB', 'HP', 'HC', 'BASE']

def check_required(config: dict[str, str], required: list[str]):
    for r in required:
        if r not in config.keys():
            raise ValueError(f'Required parameter {r} not found in {config.keys()} from .env file.')
    return config

def load_prefixed_dotenv(prefix: str='EOB_', required: list[str]=[]) -> dict[str, str]:
    # Load the .env file
    load_dotenv()

    # Retrieve all environment variables
    env_variables = dict(os.environ)
    
    return check_required({k.replace(prefix, ''): v for k, v in env_variables.items() if k.startswith(prefix)}, required)

def gen_dates(current: date | None=None) -> tuple[date, date]:
    if not current:
        current = date.today()
    
    if current.month == 1:
        current = current.replace(month=12, year=current.year-1)
    else:
        current = current.replace(month=current.month-1)

    starting_date = current.replace(day=1)
    ending_date = current.replace(day = monthrange(current.year, current.month)[1])
    return starting_date, ending_date

def gen_Timestamps(current: date | None) -> tuple[Timestamp, Timestamp]:
    start_date, ending_date = gen_dates(current)

    start_TimeStamps = pd.to_datetime(datetime.combine(start_date, datetime.min.time())).tz_localize('Etc/GMT-2')
    end_TimeStamps = pd.to_datetime(datetime.combine(ending_date, datetime.max.time())).tz_localize('Etc/GMT-2')
    return start_TimeStamps, end_TimeStamps
  
def decrypt_file(file_path: Path, key: bytes, iv: bytes, prefix: str="decrypted_") -> Path:
    if file_path.stem.startswith(prefix):
        return file_path
    
    # Initialize the AES cipher with CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    output_file = file_path.with_name(prefix + file_path.stem + ".zip")
    # Decrypt the input file and write the decrypted content to the output file
    with file_path.open("rb") as f_in, output_file.open("wb") as f_out:
        decrypted_data = cipher.decrypt(f_in.read())
        f_out.write(decrypted_data)
    return output_file

def encrypt_file(file_path: Path, key: bytes, iv: bytes, prefix: str="encrypted_") -> Path:
    if prefix in file_path.stem:
        return file_path
    # Initialize the AES cipher with CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    output_file = file_path.with_name(prefix + file_path.stem + ".enc")
    # Encrypt the input file and write the encrypted content to the output file
    with file_path.open("rb") as f_in, output_file.open("wb") as f_out:
        while True:
            data = f_in.read(16)
            if len(data) == 0:
                break
            elif len(data) % 16!= 0:
                data += b' ' * (16 - len(data) % 16)
            encrypted_data = cipher.encrypt(data)
            f_out.write(encrypted_data)
    return output_file

def recursively_decrypt_zip_files(directory: Path, key: bytes, iv: bytes, prefix:str, remove_encrypted: bool=False):
    """
    Recursively decrypts all ZIP files in the specified directory that are not already decrypted.

    Parameters:
    directory (Path): The directory to search for ZIP files.
    key (bytes): The AES key for decryption.
    iv (bytes): The AES initialization vector for decryption.
    """
    for file in directory.rglob('*.zip'):  # Recursively find all ZIP files
        if not file.stem.startswith('decrypted_'):  # Check if the file is not already decrypted
            decrypted_file_path = decrypt_file(file, key, iv, prefix=prefix)
            if remove_encrypted:
                file.unlink()  # Remove the encrypted file after decryption
                
def download_decrypt_extract(sftp: paramiko.SFTPClient, remote_file: str, output_path: Path, key: bytes, iv: bytes) -> bool:
    """
    Downloads a file from SFTP, decrypts it using decrypt_file, extracts its contents, and cleans up temporary files.

    Args:
    sftp (paramiko.SFTPClient): An active SFTP client connection.
    remote_file (str): Path to the file on the remote server.
    output_path (Path): Local path where extracted contents should be saved.
    key (bytes): 16-byte key for AES decryption.
    iv (bytes): 16-byte initialization vector for AES decryption.

    Returns:
    bool: True if successful, False otherwise.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download file
            local_encrypted_path = Path(temp_dir) / Path(remote_file).name
            sftp.get(remote_file, str(local_encrypted_path))

            # Decrypt file using decrypt_file function
            decrypted_path = decrypt_file(local_encrypted_path, key, iv)

            # Extract contents
            with zipfile.ZipFile(decrypted_path, 'r') as zip_ref:
                zip_ref.extractall(output_path)

            _logger.debug(f"Successfully processed {remote_file}")
            return True

        except paramiko.SSHException as e:
            _logger.error(f"SFTP error while downloading {remote_file}: {str(e)}")
        except ValueError as e:
            _logger.error(f"Decryption error for {remote_file}: {str(e)}")
        except zipfile.BadZipFile as e:
            _logger.error(f"ZIP extraction error for {remote_file}: {str(e)}")
        except Exception as e:
            _logger.error(f"Unexpected error processing {remote_file}: {str(e)}")

        return False

def download_decrypt_extract_new_files(
    config: dict[str, str], 
    tasks: list[str], 
    local: Path,
    force: bool = False,
    callback: Callable[[str, int, int, str], None] | None = None
) -> list[tuple[str, str]]:
    """
    Downloads, decrypts, and extracts new files from the SFTP server, skipping files that have already been processed.
    Uses a callback function for progress tracking.

    Parameters:
    config (dict[str, str]): Configuration dictionary containing SFTP details, key, and IV.
    tasks (list[str]): List of directory types to process (e.g., ['R15', 'C15']).
    local (Path): The local root path to save extracted files.
    callback (callable, optional): A function to call for progress updates. It should accept the following parameters:
                                   - task_type (str): The current task type being processed.
                                   - total_files (int): Total number of files to process.
                                   - current_file (int): Current file being processed (1-indexed).
                                   - file_name (str): Name of the current file being processed.

    Returns:
    list[tuple[str, str]]: A list of tuples containing (zip_name, task_type) of newly processed files.
    """
    required = ['FTP_ADDRESS', 'FTP_USER', 'FTP_PASSWORD', 'AES_KEY', 'AES_IV'] + [f'FTP_{k}_DIR' for k in tasks]
    config = check_required(config, required)

    key = bytes.fromhex(config['AES_KEY'])
    iv = bytes.fromhex(config['AES_IV'])

    csv_path = local / "processed_zips.csv"
    if force and csv_path.exists():
        csv_path.unlink()
    
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        processed_zips = set(df['zip_name'])
    else:
        df = pd.DataFrame(columns=['zip_name', 'flux'])
        processed_zips = set()

    transport = paramiko.Transport((config['FTP_ADDRESS'], 22))
    transport.connect(username=config['FTP_USER'], password=config['FTP_PASSWORD'])
    sftp = paramiko.SFTPClient.from_transport(transport)

    newly_processed_files = []

    try:
        for task_type in tasks:
            distant = '/flux_enedis/' + str(config[f'FTP_{task_type}_DIR'])
            local_dir = local.joinpath(task_type)
            local_dir.mkdir(parents=True, exist_ok=True)

            try:
                files_to_process = [f for f in sftp.listdir(distant) if f not in processed_zips]
                total_files = len(files_to_process)

                for index, file_name in enumerate(files_to_process, start=1):
                    if callback:
                        callback(task_type, total_files, index, file_name)

                    remote_file_path = os.path.join(distant, file_name)
                    output_path = local_dir / file_name.replace('.zip', '')
                    
                    success = download_decrypt_extract(sftp, remote_file_path, output_path, key, iv)
                    
                    if success:
                        newly_processed_files.append((file_name, task_type))
                        df = pd.concat([df, pd.DataFrame({'zip_name': [file_name], 'flux': [task_type]})], ignore_index=True)

            except Exception as e:
                _logger.error(f"Failed to process files from {distant}: {e}")

    finally:
        sftp.close()
        transport.close()

    df.to_csv(csv_path, index=False)

    return newly_processed_files

def main():
    from rich.console import Console
    from rich.progress import Progress
    from rich.panel import Panel
    # Configuration
    config = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')

    # List of tasks (directory types to process)
    tasks: list[str] = ['R15', 'C15', 'F12']

    # Local directory to save files
    local: Path = Path('~/data/flux_enedis_expe').expanduser()

    # Ensure the local directory exists
    local.mkdir(parents=True, exist_ok=True)

    # Rich console for pretty output
    console = Console()
    def simple_callback(task_type, total_files, current_file, file_name):
        print(f"Processing {task_type}: {current_file}/{total_files} - {file_name}")
    # Call the download function
    try:
        console.print(Panel("Starting file processing", style="bold blue"))
        

        newly_processed = download_decrypt_extract_new_files(
            config, tasks, local, force=False, callback=simple_callback)


        console.print(Panel("File processing completed", style="bold green"))

        # Print summary of processed files
        console.print("\n[bold]Processed files:[/bold]")
        for file_name, flux in newly_processed:
            console.print(f"- {file_name} ({flux})")

        console.print(f"\n[bold]Total files processed:[/bold] {len(newly_processed)}")

    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")

if __name__ == "__main__":
    main()