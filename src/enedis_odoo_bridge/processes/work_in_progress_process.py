import logging
import numpy as np
import pandas as pd
from pandas import DataFrame, Timestamp
from datetime import date
from pathlib import Path

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.utils import gen_dates

from enedis_odoo_bridge.enedis_flux_reader.services import get_consumptions_by_date, get_r15_by_date

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
        
    def run(self):
        starting_date = date(2024, 6, 1)
        ending_date = date(2024, 6, 3)
        enedis_flux_path : Path = Path('~/data/flux_enedis')
        data = get_consumptions_by_date(enedis_flux_path, starting_date, ending_date)

        print(data)

        get_r15_by_date(enedis_flux_path, starting_date, ending_date)


