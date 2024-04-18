import os
import zipfile
from dotenv import load_dotenv
from pathlib import Path
from sftpretty import Connection
from datetime import date
from calendar import monthrange
import hashlib
import json
from Crypto.Cipher import AES

from typing import List, Dict, Tuple, Union, Any

def gen_dates(current: Union[date, None]) -> Tuple[date, date]:
    if not current:
        current = date.today()
    
    if current.month == 1:
        current = current.replace(month=12, year=current.year-1)
    else:
        current = current.replace(month=current.month-1)

    starting_date = current.replace(day=1)
    ending_date = current.replace(day = monthrange(current.year, current.month)[1])
    return starting_date, ending_date

def pro_rata(start: date, end: date) -> float:

    if end < start or (abs(end.month-start.month)> 1 and not (end.year-start.year==1 and start.month==12 and end.month==1)):
        raise ValueError(f'Dates are not valid, end month must be same or next month of start month : {start} - {end}')
    
    if start.month == end.month:
        return (end.day-start.day+1)/monthrange(start.year, start.month)[1]
    
    x = (monthrange(start.year, start.month)[1]+1 - start.day)/monthrange(start.year, start.month)[1]
    y = (end.day)/monthrange(end.year, end.month)[1]
    return  x + y

def unzip(zip_path: Path) -> Path:
    """
    Extracts the contents of the given zip file to a specified directory.

    Parameters:
    zip_path (str): The path to the zip file to be extracted.

    Returns:
    Path: The path to the directory where the contents of the zip file were extracted.

    Raises:
    FileNotFoundError: If the specified zip file does not exist.

    This function uses the built-in `zipfile` module to extract the contents of the zip file to a specified directory. It first creates the specified directory if it does not already exist. Then, it extracts the contents of the zip file to that directory.

    Example:
    ```python
    extracted_dir = unzip('/path/to/myfile.zip')
    print(extracted_dir)  # Output: '/path/to/myfile/'
    ```
    """
    if not zip_path.exists():
        raise FileNotFoundError(f'File {zip_path} not found.')
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        out = Path(zip_path).parent.joinpath(Path(zip_path).stem)
        #print(f'creating {out} directory and extracting')
        out.mkdir(exist_ok=True)

        zip_ref.extractall(out)
        return out
    
def download(tasks: List[str], local: Path=Path('~/data/flux_enedis/')) -> Dict[str, Path]:
    """
    Downloads a specified directory from the ftp and returns the local path.

    Parameters:
    type (str): The code defining the type of flux to download. Either {R15 | C15 | F15}

    Returns:
    Path: The local path of directory containing all downloaded files.

    Raises:
    ValueError: If the specified directory type is not found in the remote_dirs dictionary.
    """
    load_dotenv()

    address = os.getenv("FTP_ADDRESS")
    username = os.getenv("FTP_USER")
    password = os.getenv("FTP_PASSWORD")
    remote_dirs = {'R15': os.getenv("FTP_R15"), 
                    'C15': os.getenv("FTP_C15"),
                    'F15': os.getenv("FTP_F15")}
    
    completed_tasks = {}
    for type in tasks:
        if not type in remote_dirs.keys():
            raise ValueError(f'Type {type} not found in {list(remote_dirs.keys())}')

        distant = '/flux_enedis/' + str(remote_dirs[type])
        local = local.joinpath(type).expanduser()

        # resume = True permet de ne pas re-télécharger les fichiers déjà téléchargés
        with Connection(address, username=username, password=password, port=22) as ftp:

            # TODO activation du Retry: [DISABLED] 
            ftp.get_d(distant, local, resume=True, workers=10)

        completed_tasks[type] = local

    return completed_tasks

def calculate_checksum(file_path: Path) -> str:
    # Initialize SHA-256 hash object
    sha256 = hashlib.sha256()

    # Open file in binary mode
    with open(file_path, "rb") as file:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: file.read(4096), b""):
            # Update hash object with current chunk
            sha256.update(chunk)

    # Return hexadecimal representation of hash
    return sha256.hexdigest()

def file_changed(file_path: Path, stored_checksum: str) -> bool:
    # Calculate checksum of current archive
    current_checksum = calculate_checksum(file_path)

    # Compare current checksum with stored checksum
    return current_checksum != stored_checksum

def is_valid_json(json_string: str) -> bool:
    try:
        # Essayez de charger le JSON
        json.loads(json_string)
    except ValueError as e:
        # Si une erreur se produit, le JSON n'est pas valide
        return False
    return True

def decrypt_file(file_path: Path, key: bytes, iv: bytes) -> Path:

    # Initialize the AES cipher with CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    output_file = file_path.with_name("decrypted_" + file_path.stem + ".zip")
    # Decrypt the input file and write the decrypted content to the output file
    with file_path.open("rb") as f_in, output_file.open("wb") as f_out:
        decrypted_data = cipher.decrypt(f_in.read())
        f_out.write(decrypted_data)
    return output_file