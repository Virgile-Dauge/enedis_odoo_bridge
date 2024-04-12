import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from sftpretty import Connection

#_logger = logging.getLogger(__name__)

class FTPCon:
    """
    Class for handling FTP connections and downloading files.

    Attributes:
        address (str): The FTP server address.
        username (str): The FTP username.
        password (str): The FTP password.
        remote_dirs (dict): A dictionary mapping directory names to their corresponding FTP paths.

    Methods:
        __init__(self): Loads environment variables.
        download(self, type: str) -> Path: Downloads a file from the specified directory and returns the local path.
    """

    def __init__(self):
        """
        Loads environment variables.
        """
        load_dotenv()

        self.address = os.getenv("FTP_ADDRESS")
        self.username = os.getenv("FTP_USER")
        self.password = os.getenv("FTP_PASSWORD")
        self.remote_dirs = {'R15': os.getenv("FTP_R15"), 
                             'C15': os.getenv("FTP_C15"),
                             'F15': os.getenv("FTP_F15")}

    def download(self, type: str) -> Path:
        """
        Downloads a file from the specified directory and returns the local path.

        Parameters:
        type (str): The code defining the type of flux to download. Either {R15 | C15 | F15}

        Returns:
        Path: The local path of directory containing all downloaded files.

        Raises:
        ValueError: If the specified directory type is not found in the remote_dirs dictionary.
        """
        if not type in self.remote_dirs.keys():
            raise ValueError(f'Type {type} not found in {self.remote_dirs.keys()}')

        local = Path('~/data/flux_enedis/').joinpath(type).expanduser()
        # resume = True permet de ne pas re-télécharger les fichiers déjà téléchargés
        with Connection(self.address, username=self.username, password=self.password, port=22) as ftp:
            ftp.get_d('/flux_enedis/'+self.remote_dirs[type], local, resume=True)
        return local.joinpath(self.remote_dirs[type])
