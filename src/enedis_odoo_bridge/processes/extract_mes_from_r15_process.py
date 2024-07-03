import logging

from pathlib import Path
from pandas import DataFrame
from datetime import date

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.enedis_flux_engine import get_r15_by_date


class ExtractMESFromR15Process(BaseProcess):
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
        self.logger.info(f"Extracting MES from R15")
        enedis_flux_path : Path = Path('~/data/flux_enedis')
        start_date = self.start_date
        end_date = self.end_date
        
        r15 = get_r15_by_date(enedis_flux_path, start_date, end_date)
        if r15.empty:
            raise ValueError(f"Aucune donnée trouvée pour les dates spécifiées: {start_date} à {end_date}")
        filter =  ((r15['Motif_Releve'] == 'CFNE') | (r15['Motif_Releve'] == 'MES')) & (r15['Ref_Demandeur'] == self.filter) #& (r15['Date_Releve'] >= start) & (r15['Date_Releve'] <= end)
        r15 = r15[filter]
        self.logger.info(f"{r15}")

        r15.to_csv(Path('./output') /
            f'Extract_MES_for_{self.filter}_{start_date}_{end_date}.csv')
