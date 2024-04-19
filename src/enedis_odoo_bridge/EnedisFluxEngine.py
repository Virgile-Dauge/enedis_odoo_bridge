
import pandas as pd
from pandas import Timestamp, DataFrame, Series
from pathlib import Path
from typing import Dict, List, Any
from datetime import date, datetime

import json

from datetime import datetime
from enedis_odoo_bridge import __version__
from enedis_odoo_bridge.utils import calculate_checksum, is_valid_json, download, decrypt_file, unzip, check_required
from enedis_odoo_bridge.R15Parser import R15Parser
from enedis_odoo_bridge.estimators import Strategy, StrategyMaxMin

import logging
_logger = logging.getLogger(__name__)

class EnedisFluxEngine:
    """
    A class for handling Enedis Flux files and allow simple access to the data.
    """
    def __init__(self, config: Dict[str,str], path:str = '~/data/enedis/', flux: List[str]=[], update:bool=False):
        """
        Initializes the EnedisFluxEngine instance with the specified path and flux types.

        :param path: A string representing the root directory for the Enedis Flux files. Defaults to '~/data/enedis/'.
        :type path: str
        :param flux: A list of strings representing the types of Enedis Flux files to be processed.
        :type flux: List[str]

        If the specified path does not exist, a FileNotFoundError is raised. The function then creates directories for each flux type if they do not already exist.

        The instance variables `root_path`, `flux`, `db`, and `data` are initialized.

        :return: None
        :rtype: None
        """
        self.config = check_required(config, ['AES_KEY', 'AES_IV', 
                                              'FTP_USER', 'FTP_PASSWORD', 'FTP_ADDRESS',
                                              'FTP_R15_DIR', 'FTP_C15_DIR', 'FTP_F15_DIR'])
        self.root_path = Path(path).expanduser()
        self.flux = flux
        self.supported_flux = ['R15']
        self.heuristic = StrategyMaxMin()
        self.key = bytes.fromhex(self.config['AES_KEY'])
        self.iv = bytes.fromhex(self.config['AES_IV'])

        for f in flux:
            if f not in self.supported_flux:
                raise ValueError(f'Flux type {f} not supported.')
        
        if not self.root_path.is_dir():
            raise FileNotFoundError(f'File {self.root_path} not found.')
        
        self.dirs = self.mkdirs()

        self.db = self.read_db()
        if update:
            self.fetch_distant()
        else:
            _logger.info(f'No fetching, using local zips only')
        self.data = self.scan()
        
    def fetch_distant(self):
        """
        Fetches the Enedis Flux files from the FTP server and decrypts them.
        """
        _logger.info(f"Fetching from ftp: {self.config['FTP_ADDRESS']}")
        download(self.config, self.flux, self.root_path)
        self.decrypt()
    
    def decrypt(self):
        """
        Decrypts the specified ZIP files containing Enedis Flux data.

        :param self: Instance of the EnedisFluxEngine class.
        :return: None

        This function first identifies the ZIP files that need to be decrypted by checking if the file name already contains the prefix "decrypted_".
        It then iterates through each ZIP file, decrypting it using the provided AES key and initialization vector.
        The decrypted files are saved in the same directory as the original ZIP files, with the prefix "decrypted_" added to their names.
        """
        to_process = [file for k in self.flux for file in self.root_path.joinpath(k).glob("*.zip") if "decrypted_" not in file.stem]
        for f in to_process:
            decrypt_file(f, self.key, self.iv)
        _logger.info(f"└── {len(to_process)} new ZIP files decrypted.")

    def scan(self) -> Dict[str, pd.DataFrame]:
        """
        Scans the specified directories for the given flux types and processes the ZIP files.

        :param self: Instance of the EnedisFluxEngine class.
        :return: A dictionary containing DataFrames for each processed flux type.

        The function first retrieves the directories for each flux type and the list of ZIP files in each directory.
        It then iterates through each flux type, checking for any new files that have not been processed yet.
        The already processed DataFrame is then loaded from the corresponding CSV file if it exists.
        If there are new files, it creates a new DataFrame by parsing the contents of each ZIP file and concatenating them.
        It concatenates already processed DataFrames with the new one if necessary.
        The resulting DataFrame is then saved as a CSV file in the corresponding directory.
        The function also updates the 'light_db.json' file with the latest checksums of processed ZIP files.
        """
        directories = [self.root_path.joinpath(k) for k in self.flux]
        to_process = {k: [a for a in self.root_path.joinpath(k).glob('*.zip') if 'decrypted_' in a.stem] for k in self.flux}

        _logger.info(f'Scanning {self.root_path} for flux {self.flux}')
        res = {}
        for (flux_type, archives), working_path in zip(to_process.items(), directories):

            # Récupération du travail déjà fait :
            already_processed = self.db[flux_type]['already_processed']
            #csv = working_path.joinpath(f'{flux_type}.csv')
            #r15 = pd.read_csv(csv) if csv.is_file() else None
            pkl = working_path.joinpath(f'{flux_type}.pkl')
            r15 = pd.read_pickle(pkl) if pkl.is_file() else None

            checksums = [calculate_checksum(a) for a in archives]
            to_add = [a for a, c in zip(archives, checksums) if c not in already_processed]
            
            if not to_add:
                if r15 is not None:
                    res[flux_type] = r15
                _logger.info(f'└── No new zip for {flux_type}, using past {len(already_processed)} zips.')
                continue
            # TODO adaptation dynamique en fonction du type de flux
            parsed = [R15Parser(a) for a in to_add]
            
            concat = pd.concat([p.data for p in parsed])

            if r15 is not None:
                concat = pd.concat([r15, concat])
            
            # Tri par date, par pdl, puis du plus vieux au plus récent :
            concat = concat.sort_values(by=['pdl', 'Date_Releve'])
            concat = concat.reset_index(drop=True)
            concat.to_pickle(working_path.joinpath(f'{flux_type}.pkl'))
            concat.to_csv(working_path.joinpath(f'{flux_type}.csv'))

            # Maj des cheksum pour ne pas reintégrer les fichiers
            newly_processed = [c for a, c in zip(archives, checksums) if c not in already_processed]
            self.db[flux_type]['already_processed'] = already_processed + newly_processed
            _logger.info(f'Added : {to_add}')

            self.update_db()
            res[flux_type] = concat
            concat.to_csv(working_path.joinpath(f'{flux_type}.csv'))
            concat.to_pickle(working_path.joinpath(f'{flux_type}.pkl'))

            # Maj des cheksum pour ne pas reintégrer les fichiers
            newly_processed = [c for a, c in zip(archives, checksums) if c not in already_processed]
            self.db[flux_type]['already_processed'] = already_processed + newly_processed
            _logger.info(f'Added : {to_add}')

            self.update_db()
            res[flux_type] = concat
        return res
    
    def mkdirs(self) -> Dict[str, Path]:
        """
        Creates directories for each flux type if they do not already exist.

        :param self: Instance of the EnedisFluxEngine class.
        :return: None
        """
        dirs = {k: self.root_path.joinpath(k) for k in self.flux}
        for k, v in dirs.items():
            v.mkdir(exist_ok=True)
        return dirs
    
    def read_db(self) -> Dict[str, Dict[str, Any]]:
        """
        Reads the 'light_db.json' files for each flux type and returns a dictionary containing the data of all parsed JSON.

        :param self: Instance of the EnedisFluxEngine class.
        :return: A dictionary containing the parsed JSON data for each flux type.
        """
        jsons = {k: list(self.root_path.joinpath(k).glob('light_db.json'))for k in self.flux}
        db = {k: json.loads(v[0].read_text()) for k, v in jsons.items() if v and is_valid_json(v[0].read_text())}

        for f in self.flux:
            if f not in db:
                db[f] = {'already_processed': []}
        _logger.debug(f'Loaded light_db: {db}')
        return db
    
    def update_db(self) -> None:
        """
        Updates the light_db.json file for each flux type with the latest checksums of processed zips.

        :param self: Instance of the EnedisFluxEngine class.
        :return: None
        """
        for k, v in self.db.items():
            self.root_path.joinpath(k).joinpath('light_db.json').write_text(json.dumps(v))

    def estimate_consumption(self, start: date, end: date) -> pd.DataFrame:
        """
        Estimates the total consumption per PDL for the specified period, according to the EnedisFluxEngine set Strategy.

        :param self: Instance of the EnedisFluxEngine class.
        :param start: The start date of the period.
        :type start: date
        :param end: The end date of the period.
        :type end: date
        :return: The total consumption for the specified period, on each 
        :rtype: pd.DataFrame

        On affiche l'estimation commandée,
        On appelle la fonction estimate_consumption de la stratégie définie.
        On affiche un rapport de l'estimation.
        On retourne la liste des consommations pour chaque PDL.
        """
        
        if not self.data:
            raise ValueError(f'No data found, try fetch then scan first.')
        # On veut inclure les journées de début et de fin de la période.
        start_pd = pd.to_datetime(datetime.combine(start, datetime.min.time()))
        end_pd = pd.to_datetime(datetime.combine(end, datetime.max.time()))

        _logger.info(f'Estimating consumption: from {start_pd} to {end_pd}')
        _logger.info(f'With {self.heuristic.get_strategy_name()} Strategy.')

        consos = self.heuristic.estimate_consumption(self.data, start_pd, end_pd)

        if len(consos)>0:
            _logger.info(f"└── Succesfully Estimated consumption of {len(consos)} PDLs.")
        else:
            _logger.warn(f"└── Failed to Estimate consumption of any PDLs.")
        consos.to_csv(self.root_path.joinpath('R15').joinpath(f'estimated_consumption_from_{start}_to{end}.csv'))
        return consos
    
    def enrich_estimates(self, estimates: pd.DataFrame, columns: List[str])-> pd.DataFrame:
        for k in columns:
            if k not in self.data['R15'].columns:
                raise ValueError(f'Asked column {k} not found in R15 data.')
        to_add = self.data['R15'][['pdl']+columns].drop_duplicates(subset='pdl', keep='first')
        return pd.merge(estimates, to_add, how='left', on='pdl')
    
    def fetch(self, start: date, end: date, columns: List[str], heuristic: Strategy=StrategyMaxMin()):
        estimates = self.estimate_consumption(start, end)
        return self.enrich_estimates(estimates, columns)