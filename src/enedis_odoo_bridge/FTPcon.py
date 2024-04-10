import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from sftpretty import Connection

#_logger = logging.getLogger(__name__)


class FTPCon:
    def __init__(self):
        load_dotenv()

        self.address = os.getenv("FTP_ADDRESS")
        self.username = os.getenv("FTP_USER")
        self.password = os.getenv("FTP_PASSWORD")
        self.remote_dirs = {'R15': os.getenv("FTP_R15"), 
                     'C15': os.getenv("FTP_C15"),
                     'F15': os.getenv("FTP_F15")}

    def download(self, type: str) -> Path:
        with Connection(self.address, username=self.username, password=self.password, port=22) as ftp:
            if not type in self.remote_dirs.keys():
                raise ValueError(f'Type {type} not found in {self.remote_dirs.keys()}')
            
            local = Path('~/data/flux_enedis/').joinpath(type).expanduser()
            # resume = True permet de ne pas re-télécharger les fichiers déjà téléchargés
            ftp.get_d('/flux_enedis/'+self.remote_dirs[type], local, resume=True)
        return local.joinpath(self.remote_dirs[type])
