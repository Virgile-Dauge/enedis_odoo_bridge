from datetime import date
import logging
from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine


class ExtractMESFromR15Process(BaseProcess):
    def __init__(self, filter: str, 
                 config: dict[str, str], enedis: EnedisFluxEngine, date: date, 
                 logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:
        super().__init__(config, enedis) 
        self.filter = filter
        
    def run(self):
        self.logger.info(f"Extracting MES from R15")
        enedis_data = self.enedis.scan()

        meta = enedis_data['R15'].get_meta()

        filter =  ((meta['Motif_Releve'] == 'CFNE') | (meta['Motif_Releve'] == 'MES')) & (meta['Ref_Demandeur'] == self.filter) #& (r15['Date_Releve'] >= start) & (r15['Date_Releve'] <= end)

        data = enedis_data['R15'].data[filter]

        data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'Extract_MES_for_{self.filter}.csv'))