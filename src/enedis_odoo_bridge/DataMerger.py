from typing import Dict, List
from datetime import date

from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.utils import gen_dates, check_required


class DataMerger:
    def __init__(self, config: Dict[str, str], date:date, enedis: EnedisFluxEngine, odoo: OdooAPI) -> None:
        self.config = check_required(config, [])
        self.enedis = enedis
        self.odoo = odoo

        self.starting_date, self.ending_date = gen_dates(date)


    def fetch_enedis_data(self):
        # Récupérer les données depuis EnedisFluxEngine
        return self.enedis.estimate_consumption(self.starting_date, self.ending_date)

    def fetch_odoo_data(self):
        # Récupérer les données depuis OdooAPI
        return self.odoo.get_drafts()

    def merge_data(self, enedis_data, odoo_data):
        # Fusionner les données ici
        pass

    def update_odoo(self, merged_data):
        # Mettre à jour Odoo avec les données fusionnées
        self.odoo.update_data(merged_data)

    def process(self):
        enedis_data = self.fetch_enedis_data()
        odoo_data = self.fetch_odoo_data()
        merged_data = self.merge_data(enedis_data, odoo_data)
        #self.update_odoo(merged_data)


