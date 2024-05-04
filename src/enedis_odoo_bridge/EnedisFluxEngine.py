
import pandas as pd
from pathlib import Path
from typing import Any
from datetime import date, datetime
from rich import inspect
from pandas import Timestamp
from datetime import datetime
from enedis_odoo_bridge import __version__
from enedis_odoo_bridge.utils import check_required, recursively_decrypt_zip_files, recursively_decrypt_zip_files, download_new_files

from enedis_odoo_bridge.consumption_estimators import BaseEstimator, LastFirstEstimator
from enedis_odoo_bridge.flux_transformers import FluxTransformerFactory, BaseFluxTransformer

import logging

class EnedisFluxEngine:
    """
    A class for handling Enedis Flux files and allow simple access to the data.
    """
    def __init__(self, config: dict[str,str], path: Path, flux: list[str], logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')):
        """
        Initializes the EnedisFluxEngine instance with the specified path and flux types.

        :param path: A string representing the root directory for the Enedis Flux files.
        :type path: str
        :param flux: A list of strings representing the types of Enedis Flux files to be processed.
        :type flux: list[str]

        If the specified path does not exist, a FileNotFoundError is raised. The function then creates directories for each flux type if they do not already exist.

        The instance variables `root_path`, `flux`, are initialized.

        :return: None
        :rtype: None
        """
        self.logger = logger
        self.config = check_required(config, ['AES_KEY', 'AES_IV', 
                                              'FTP_USER', 'FTP_PASSWORD', 'FTP_ADDRESS',
                                              'FTP_R15_DIR', 'FTP_C15_DIR', 'FTP_F15_DIR'])
        self.root_path = path
        if not self.root_path.is_dir():
            raise FileNotFoundError(f'File {self.root_path} not found.')
        
        self.flux = flux
            
        self.heuristic = None
        self.key = bytes.fromhex(self.config['AES_KEY'])
        self.iv = bytes.fromhex(self.config['AES_IV'])
        
    def fetch_distant(self):
        """
        Fetches the Enedis Flux files from the FTP server and decrypts them.
        """
        self.logger.info(f"Fetching from ftp: {self.config['FTP_ADDRESS']}")
        download_new_files(self.config, self.flux, self.root_path)
        recursively_decrypt_zip_files(self.root_path, self.key, self.iv, prefix='decrypted_')

    def scan(self) -> dict[str, pd.DataFrame]:
        """
        Scans the specified directories for the given flux types and processes the ZIP files.

        :param self: Instance of the EnedisFluxEngine class.
        :return: A dictionary containing DataFrames for each processed flux type.

        The function first retrieves the directories for each flux type and the list of ZIP files in each directory.
        It then iterates through each flux type, checking for any new files.
        If there is new files, it creates a new DataFrame by parsing the contents of each ZIP file and concatenating them.
        It concatenates already processed DataFrames with the new one if necessary.
        The resulting DataFrame is then saved as a CSV file in the corresponding directory.
        The function also updates the 'light_db.json' file with the latest checksums of processed ZIP files.
        """
        directories = [self.root_path.joinpath(k) for k in self.flux]
        to_process = {k: [a for a in self.root_path.joinpath(k).glob('*.zip') if 'decrypted_' in a.stem] for k in self.flux}

        self.logger.info(f'Scanning {self.root_path} for flux {self.flux}')
        self.logger.extra['prefix'] = '│  '

        res = {}
        for (flux_type, archives), working_path in zip(to_process.items(), directories):

            factory = FluxTransformerFactory()
            flux_transformer = factory.get_transformer(flux_type)
            for a in archives:
                flux_transformer.add_zip(a)

            flux = flux_transformer.preprocess()
            flux.to_csv(working_path.joinpath(f'{flux_type}.csv'))

            self.logger.info(f'├──Added : {len(archives)} zip files for {flux_type}')

            res[flux_type] = flux_transformer
        self.logger.info(f'└──Scan done.')
        return res
    def estimate_consumption(self, start: Timestamp, end: Timestamp, heuristic: BaseEstimator) -> pd.DataFrame:
        """
        Estimates the total consumption per PDL for the specified period, according to the given estimator.

        :param self: Instance of the EnedisFluxEngine class.
        :param start: The start date of the period.
        :type start: date
        :param end: The end date of the period.
        :type end: date
        :return: The total consumption for the specified period, on each 
        :rtype: pd.DataFrame

        On affiche l'estimation commandée,
        On appelle la fonction estimate_consumption de l'estimateur choisi
        On affiche un rapport de l'estimation.
        On retourne la liste des consommations pour chaque PDL.
        """
        
        if not self.data:
            raise ValueError(f'No data found, try fetch then scan first.')

        self.logger.info(f'Estimating consumption: from {start} to {end}')
        self.logger.extra['prefix'] = '│  '
        self.logger.info(f'└──With {heuristic.get_estimator_name()} Strategy.')

        meta = self.data['R15'].get_meta()
        index = self.data['R15'].get_index()
        consu = self.data['R15'].get_consu()
        consos = heuristic.fetch(meta, index, consu, start, end)

        if len(consos)>0:
            self.logger.info(f"    └──Succesfully Estimated consumption of {len(consos)} PDLs.")
        else:
            self.logger.warn(f"    └──Failed to Estimate consumption of any PDLs.")
        return consos
    
    def enrich_estimates(self, estimates: pd.DataFrame, columns: list[str])-> pd.DataFrame:
        meta = self.data['R15'].get_meta()
        #columns = [c for c in self.data['R15'].columns if c[2] in columns]
        for k in columns:
            if k not in meta.columns:
                raise ValueError(f'Asked column {k} not found in R15 data.')
        to_add = meta[['pdl']+columns].drop_duplicates(subset='pdl', keep='first')
        return pd.merge(estimates, to_add, how='left', on='pdl')
    
    def fetch_estimates(self, start: Timestamp, end: Timestamp, columns: list[str], heuristic: BaseEstimator)-> pd.DataFrame:
        """
        Fetches and enriches the estimated consumption data for a specified period and set of columns.

        This method first estimates the total consumption per PDL (Point de Livraison) for the given period using the specified heuristic strategy. 
        It then enriches these estimates with additional data columns from the R15 dataset.

        :param start: The start date of the period for which consumption is to be estimated.
        :type start: date
        :param end: The end date of the period for which consumption is to be estimated.
        :type end: date
        :param columns: A list of column names from the R15 dataset to be added to the estimated consumption data.
        :type columns: list[str]
        :param heuristic: The estimator to be used for estimating consumption.
        :type heuristic: BaseEstimator
        :return: A pandas DataFrame containing the estimated consumption for each PDL, enriched with the specified columns from the R15 data.
        :rtype: pd.DataFrame
        """
        self.logger.extra['prefix'] = '├──'
        self.data = self.scan()

        self.logger.extra['prefix'] = '├──'
        estimates = self.estimate_consumption(start, end, heuristic)

        self.logger.extra['prefix'] = '├──'
        estimates = self.enrich_estimates(estimates, columns)
        return estimates
    

    def fetch_services(self, start: date, end: date)-> pd.DataFrame:
        data = self.scan()['F15'].data
        
        services = data[(data.Date_Fin >= start) & (data.Date_Fin <= end) & (data.Type_Facturation == 'EVNT')]
        return services

