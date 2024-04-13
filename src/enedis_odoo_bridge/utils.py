import os
import zipfile
from dotenv import load_dotenv
from pathlib import Path
from sftpretty import Connection

from typing import List, Dict

def unzip(zip_path: str) -> Path:
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
    if not Path(zip_path).exists():
        raise FileNotFoundError(f'File {zip_path} not found.')
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        out = Path(zip_path).parent.joinpath(Path(zip_path).stem)
        #print(f'creating {out} directory and extracting')
        out.mkdir(exist_ok=True)
        zip_ref.extractall(out)
        return out
    
def download(tasks: List[str]) -> Dict[str, Path]:
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
            raise ValueError(f'Type {type} not found in {remote_dirs.keys()}')

        distant = '/flux_enedis/' + str(remote_dirs[type])
        local = Path('~/data/flux_enedis/').joinpath(type).expanduser()

        # resume = True permet de ne pas re-télécharger les fichiers déjà téléchargés
        with Connection(address, username=username, password=password, port=22) as ftp:
            ftp.get_d(distant, local, resume=True)

        completed_tasks[type] = local

    return completed_tasks
