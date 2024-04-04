from dotenv import load_dotenv
import os
import xmlrpc.client
from xmlrpc.client import MultiCall

from pathlib import Path
from typing import Dict, List

import logging
_logger = logging.getLogger(__name__)

class OdooAPI:
    def __init__(self):
        load_dotenv()

        self.url = os.getenv("URL")
        self.db = os.getenv("DB")
        self.username = os.getenv("USERNAME")
        self.password = os.getenv("PASSWORD")

        with xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common') as common:
            #common.version()
            self.uid = common.authenticate(self.db, self.username, self.password, {})

        self.proxy = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        # Récup des logs des appels de scripts précédents
        
        logs = self.execute('x_log_enedis', 'search_read', [[]], {'fields': ['x_name']})
        self.log_history = [Path(l['x_name']).stem for l in logs]

    def execute(self, model: str, method: str, *args, **kwargs) -> List:
        return self.proxy.execute_kw(self.db, self.uid, self.password, model, method, *args, **kwargs)
    
    def get_drafts(self)-> Dict:
        # TODO ajouter un booléen dans odoo qui dit si c'est une facture d'énergie ou non
        # ['x_isTruc', '=', 'True']
        drafts = self.execute('account.move', 'search_read', 
        [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'],]], 
        {'fields': ['invoice_line_ids', 'date', 'x_order_id', ]})
        bon_ids = [d['x_order_id'][0] for d in drafts]
        # Récupération des PDL
        bons = self.execute('sale.order', 'read', [bon_ids], {'fields': ['x_pdl']})
        #print(bons)
        _logger.info(f'{len(drafts)} drafts invoices found.')
        return [d|{'pdl': p['x_pdl']} for d, p in zip(drafts, bons)] #if len(b['x_pdl'])==14

        

