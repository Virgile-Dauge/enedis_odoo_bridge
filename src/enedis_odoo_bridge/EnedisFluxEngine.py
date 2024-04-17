
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import json

from rich.pretty import pretty_repr

from datetime import datetime
from enedis_odoo_bridge import __version__
from enedis_odoo_bridge.utils import calculate_checksum, is_valid_json
from enedis_odoo_bridge.R15Parser import R15Parser

import logging
_logger = logging.getLogger(__name__)

class EnedisFluxEngine:
    """
    A class for handling Enedis Flux files and allow simple access to the data.
    """
    def __init__(self, path:str = '~/data/enedis/', flux: List[str]=[]):

        self.root_path = Path(path).expanduser()
        self.flux = flux

        
        if not self.root_path.is_dir():
            raise FileNotFoundError(f'File {self.root_path} not found.')
        
        self.create_dirs()

        self.db = self.read_db()
        self.data = self.scan()
        

    
    def scan(self) -> Dict[str, pd.DataFrame]:
        directories = [self.root_path.joinpath(k) for k in self.flux]
        to_process = {k: list(self.root_path.joinpath(k).glob('*.zip')) for k in self.flux}

        _logger.info(f'Scanning {self.root_path} for flux {self.flux}')
        res = {}
        for (flux_type, archives), working_path in zip(to_process.items(), directories):

            # Récupération du travail déjà fait :
            already_processed = self.db[flux_type]['already_processed']
            csv = working_path.joinpath(f'{flux_type}.csv')
            r15 = pd.read_csv(csv) if csv.is_file() else None

            checksums = [calculate_checksum(a) for a in archives]
            to_add = [a for a, c in zip(archives, checksums) if c not in already_processed]
            
            if not to_add:
                if r15 is not None:
                    res[flux_type] = r15
                _logger.info(f'No new files for {flux_type}')
                continue
            # TODO adaptation dynamique en fonction du type de flux
            parsed = [R15Parser(a) for a in to_add]
            
            concat = pd.concat([p.data for p in parsed])

            if r15 is not None:
                concat = pd.concat([r15, concat])
            concat.to_csv(working_path.joinpath(f'{flux_type}.csv'))

            # Maj des cheksum pour ne pas reintégrer les fichiers
            newly_processed = [c for a, c in zip(archives, checksums) if c not in already_processed]
            self.db[flux_type]['already_processed'] = already_processed + newly_processed
            _logger.info(f'Scanned : {to_add}')

            self.update_db()
            res[flux_type] = concat
        return res
    
    def create_dirs(self) -> None:
        for k in self.flux:
            if not self.root_path.joinpath(k).is_dir():
                self.root_path.joinpath(k).mkdir()
    def read_db(self) -> Dict[str, Dict[str, Any]]:
        jsons = {k: list(self.root_path.joinpath(k).glob('light_db.json'))for k in self.flux}
        db = {k: json.loads(v[0].read_text()) for k, v in jsons.items() if v and is_valid_json(v[0].read_text())}

        for f in self.flux:
            if f not in db:
                db[f] = {'already_processed': []}
        _logger.debug(f'Loaded light_db: {db}')
        return db
    
    def update_db(self):
        for k, v in self.db.items():
            self.root_path.joinpath(k).joinpath('light_db.json').write_text(json.dumps(v))
