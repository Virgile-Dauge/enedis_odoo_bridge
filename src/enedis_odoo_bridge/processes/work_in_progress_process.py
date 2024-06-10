import logging
import numpy as np
import pandas as pd
from pandas import DataFrame, Timestamp
from datetime import date, datetime
from pathlib import Path

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.utils import gen_dates

from enedis_odoo_bridge.enedis_flux_engine import get_consumptions_by_date, get_r15_by_date, get_f15_by_date

class WorkInProgressProcess(BaseProcess):
    def __init__(self,
                config: dict[str, str],
                odoo: OdooAPI,
                date: date,
                logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:
        super().__init__(config, None) 
        self.filter = filter
        self.odoo = odoo
        self.will_update_production_db = False
        
    def run(self) -> None:
        starting_date = date(2024, 5, 1)
        ending_date = date(2024, 6, 10)
        enedis_flux_path : Path = Path('~/data/flux_enedis')
        """
        data = get_consumptions_by_date(enedis_flux_path, starting_date, ending_date)
        Path('./output').mkdir(exist_ok=True)
        data.to_csv(Path('./output/consommations.csv'))

        print(data)
        """
        r15 : DataFrame = get_r15_by_date(enedis_flux_path, starting_date, ending_date)
        
        #print(r15.columns)
        r15['Date_Releve'] = pd.to_datetime(r15['Date_Releve']).apply(lambda x: x.date())
        r15['horodate'] = pd.to_datetime(r15['zip_file'].apply(lambda x: Path(x).stem.split('_')[-1]))
        r15['horodate'] = r15['horodate'].apply(lambda x: x.date())


        
        print([c for c in r15.columns if c.startswith('conso')])
        
        r15.to_csv(Path(f'./output/releves_{starting_date}_to_{ending_date}.csv'))

        unique_dates_by_zip = r15.groupby('horodate')['Date_Releve'].unique()
        #unique_dates_by_zip = r15.groupby('zip_file')['Date_Releve'].unique()
        print(unique_dates_by_zip)
        unique_dates_by_zip.to_csv(Path('./output/dates_par_zip.csv'))

        #f15 : DataFrame = get_f15_by_date(enedis_flux_path, starting_date, ending_date)
        #f15.to_csv(Path('./output/facturations.csv'))
        #print(f15)

