import logging

from pathlib import Path
from pandas import DataFrame
from datetime import date

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.enedis_flux_engine import get_f15_by_date


class ExtractServicesFromF15Process(BaseProcess):
    def __init__(self, filter: str, 
                 start_date: date,
                 end_date: date,
                 logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:
        self.start_date = start_date
        self.end_date = end_date
        self.filter = filter
        self.will_update_production_db = False
        self.logger = logger
        
    def run(self):
        self.logger.info(f"Extracting Services from F15")
        enedis_flux_path : Path = Path('~/data/flux_enedis')
        start_date = self.start_date
        end_date = self.end_date
        
        f15 = get_f15_by_date(enedis_flux_path, start_date, end_date)
        # self.logger.info(f"{f15}")
        #filter =  (f15['Ref_Demandeur'] == self.filter)
        #f15 = f15[filter]
        self.logger.info(f"{f15}")

        f15.to_csv(Path('./output') /
            f'Extract_Services_for_{self.filter}_{start_date}_{end_date}.csv')
