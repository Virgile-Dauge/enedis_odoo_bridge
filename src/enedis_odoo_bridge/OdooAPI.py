from dotenv import load_dotenv
import os
import xmlrpc.client
from xmlrpc.client import MultiCall
import numpy as np
from pathlib import Path
from typing import Dict, List
import pandas as pd

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
        _logger.info(f'{len(self.log_history)} x_log_enedis found in Odoo db.')

        self.drafts = self.get_drafts()

    def execute(self, model: str, method: str, *args, **kwargs) -> List:
        res = self.proxy.execute_kw(self.db, self.uid, self.password, model, method, *args, **kwargs)
        return res if isinstance(res, list) else [res]
    
    def get_drafts(self)-> List[Dict]:
        drafts = self.execute('account.move', 'search_read', 
        [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]]], 
        {'fields': ['invoice_line_ids', 'date', 'x_order_id']})

        # Récupération des PDL
        bons = self.execute('sale.order', 'read', 
                            [[d['x_order_id'][0] for d in drafts]], 
                            {'fields': ['x_pdl', 'x_puissance_souscrite']})

        _logger.info(f'{len(drafts)} drafts invoices found.')
        #_logger.info(drafts)

        # On ajoute le PDL à chaque facture d'énergie
        return [d|{'pdl': b['x_pdl'], 'puissance_souscrite': int(b['x_puissance_souscrite'])} for d, b in zip(drafts, bons)]
    
    def get_lines(self)-> List[Dict]:
        # On crée une liste de tuples (l, d_id)
        lines = [(l, d['id'], d['pdl']) for d in self.drafts for l in d['invoice_line_ids']]
        lines_ids, drafts_id, pdls = zip(*lines)
        lines = self.execute('account.move.line', 'read', [lines_ids],
                        {'fields': ['name', 'product_id', 'ref']})
        prods_id = [l['product_id'][0] if l['product_id'] else False for l in lines]
        #_logger.info(prods_id)
        prods = self.execute('product.product', 'read', [prods_id],
                        {'fields': ['default_code']})
        codes = [p['default_code'] for p in prods]
        #_logger.info(codes)

        # On veut une dataframe|liste dict avec en ID les PDL, une colone ID_line, une colonne code_line
        _logger.info(f'{len(codes)} account.move.line found in Odoo db.')
        return [{'id': l['id'], 'name': l['name'], 'code': c, 'pdl': p} for l, c, p in zip(lines, codes, pdls)]

    def write(self, model: str, entries: Dict[str, str])-> List[int]:
        """
        Writes entries in the Odoo database.

        Args:
            log (Dict[str, str]): A dictionary containing the entries data.

        Returns:
            int: The ID of the newly created entries in the Odoo database.

        """
        id = self.execute(model, 'create', [entries])
        if not isinstance(id, list):
            id = [int(id)]
        _logger.info(f'{model} #{id} created in Odoo db.')
        return id

    def update(self, model: str, entries: List[Dict[str, str]])-> None:
        id = []
        for e in entries:
            i = int(e['id'])
            del e['id']
            print([[i], {k: int(v) if isinstance(v, np.int64) else v for k, v in e.items()}])
            self.execute(model, 'write', [[i], {k: int(v) if isinstance(v, np.int64) else v for k, v in e.items()}])
            id += [i]

        _logger.info(f'{model} #{id} writen in Odoo db.')
    def write_releves(self, releves: pd.DataFrame)-> List[int]:
        print(releves.columns)
        return [0]
        

