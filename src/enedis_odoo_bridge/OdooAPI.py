import xmlrpc.client
from xmlrpc.client import MultiCall
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from pandas import DataFrame

from enedis_odoo_bridge.utils import check_required

import logging
_logger = logging.getLogger(__name__)

class OdooAPI:
    def __init__(self, config: Dict[str, str], sim=False):

        config = check_required(config, ['URL', 'DB', 'USERNAME', 'PASSWORD'])
        self.url = config['URL']
        db = config['DB']
        self.db = db + '-duplicate' if sim else db
        self.username = config['USERNAME']
        self.password = config['PASSWORD']

        self.uid = self.get_uid()

        self.proxy = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        _logger.info(f'logged to {self.db} Odoo db.')
        # Récup des logs des appels de scripts précédents
        
        # DEPRECATED, pas de logs dans la base Odoo car trop chiant
        #logs = self.execute('x_log_enedis', 'search_read', [[]], {'fields': ['x_name']})
        #self.log_history = [Path(l['x_name']).stem for l in logs]
        #_logger.info(f'{len(self.log_history)} x_log_enedis found in Odoo db.')

        #self.drafts = self.get_drafts()
    def get_uid(self):
        common_proxy = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        return common_proxy.authenticate(self.db, self.username, self.password, {})
    
    def execute(self, model: str, method: str, *args, **kwargs) -> List:
        res = self.proxy.execute_kw(self.db, self.uid, self.password, model, method, *args, **kwargs)
        return res if isinstance(res, list) else [res]
    
    def fetch(self)-> DataFrame:
        data = self.get_drafts(['invoice_line_ids', 'date', 'x_order_id'])
        print(data)
        data = self.add_order_fields(data, ['x_pdl', 'x_puissance_souscrite'])
        print(data)
        data = self.add_cat_fields(data, [])
        return self.clear(data)
        #return self.add_lines(self.add_orders(self.get_drafts()))
    
    def clear(self, data: DataFrame)-> DataFrame:
        return data
        #TODO : Remove all non scalar coluns from the data

    def get_drafts(self, fields: List[str])-> DataFrame:
        _logger.info(f'Searching drafts invoices in {self.url} db.')
        drafts = self.execute('account.move', 'search_read', 
            [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]]], 
            {'fields': fields})
        return DataFrame(drafts)

    def add_order_fields(self, data: DataFrame, fields: List[str])-> DataFrame:
        if 'x_order_id' not in data.columns:
            raise ValueError(f'No x_order_id found in {data.columns}')
        
        orders = self.execute('sale.order', 'read', 
                            [[d[0] for d in data['x_order_id'].to_list()]], 
                            {'fields': fields})
        df = DataFrame(orders)
        data[fields] = df[fields]
        return data
           
    def add_cat_fields(self, data: DataFrame, fields: List[str])-> DataFrame:
        if 'invoice_line_ids' not in data.columns:
            raise ValueError(f'No invoice_line_ids found in {data.columns}')
        #print(data.explode('invoice_line_ids'))
        lines = self.execute('account.move.line', 'read', data['invoice_line_ids'].to_list(),
                        {'fields': ['name', 'product_id', 'ref']})
        print(lines)
        prods_id = [l['product_id'][0] if l['product_id'] else False for l in lines]
        #_logger.info(prods_id)
        prods = self.execute('product.product', 'read', [prods_id],
                        {'fields': ['categ_id']})
        cat = [p['categ_id'][1].split(' ')[-1] for p in prods]
        df_exploded = data.explode('invoice_line_ids')
        df_exploded['cat'] = cat

        # Adding a sequence number within each 'id' group for new data
        df_exploded['seq_num'] = df_exploded.groupby('id').cumcount() + 1
        print(df_exploded)

        # Pivoting to transform 'cat' values into separate columns
        df_pivoted = df_exploded.pivot(index='id', columns='cat', values='invoice_line_ids').reset_index()
        # Renaming columns to reflect the source of the data
        df_pivoted.columns = ['id'] + [f'line_id_{x}' for x in df_pivoted.columns if x != 'id']
        print(df_pivoted)
        # Merge the pivoted DataFrame with the original DataFrame
        df_final = pd.merge(data, df_pivoted, on='id', how='left')
        return df_final

    def get_drafts_old(self)-> DataFrame:
        _logger.info(f'Searching drafts invoices in {self.url} db.')
        drafts = self.execute('account.move', 'search_read', 
        [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]]], 
        {'fields': ['invoice_line_ids', 'date', 'x_order_id']})

        # Récupération des PDL et la puissance souscrite dans les bons de commandes.
        bons = self.execute('sale.order', 'read', 
                            [[d['x_order_id'][0] for d in drafts]], 
                            {'fields': ['x_pdl', 'x_puissance_souscrite']})

        for d in drafts:
            d['x_order_id'] = d['x_order_id'][0]
        _logger.info(f'└── {len(drafts)} drafts invoices found.')
        #_logger.info(drafts)

        # TODO ajouter des colones pour les id de lignes HP, HC, BASE, et éventuellement turpe ?
        # On ajoute le PDL et la puissance souscrite à chaque facture d'énergie.
        return DataFrame([d|{'pdl': b['x_pdl'], 'puissance_souscrite': int(b['x_puissance_souscrite'])} for d, b in zip(drafts, bons)])
    
    def get_lines(self)-> DataFrame:
        drafts = self.execute('account.move', 'search_read', 
        [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]]], 
        {'fields': ['invoice_line_ids', 'date', 'x_order_id']})

                # Récupération des PDL et la puissance souscrite dans les bons de commandes.
        bons = self.execute('sale.order', 'read', 
                            [[d['x_order_id'][0] for d in drafts]], 
                            {'fields': ['x_pdl', 'x_puissance_souscrite']})
        drafts = [d|{'pdl': b['x_pdl'], 'puissance_souscrite': int(b['x_puissance_souscrite'])} for d, b in zip(drafts, bons)]
        # On crée une liste de tuples (l, d_id)
        lines = [(l, d['id'], d['pdl']) for d in drafts for l in d['invoice_line_ids']]
        lines_ids, drafts_id, pdls = zip(*lines)
        lines = self.execute('account.move.line', 'read', [lines_ids],
                        {'fields': ['name', 'product_id', 'ref']})
        prods_id = [l['product_id'][0] if l['product_id'] else False for l in lines]
        #_logger.info(prods_id)
        prods = self.execute('product.product', 'read', [prods_id],
                        {'fields': ['default_code', 'categ_id']})
        print(prods)
        codes = [p['default_code'] for p in prods]
        #_logger.info(codes)

        # On veut une dataframe|liste dict avec en ID les PDL, une colone ID_line, une colonne code_line
        _logger.info(f'{len(codes)} account.move.line found in Odoo db.')
        return DataFrame([{'id': l['id'], 'name': l['name'], 'code': c, 'pdl': p} for l, c, p in zip(lines, codes, pdls)])

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
            data = e
            data = {k: int(v) if isinstance(v, np.int64) else v for k, v in data.items()}
            data = {k: float(v) if isinstance(v, np.float64) else v for k, v in data.items()}
            self.execute(model, 'write', [[i], data])
            id += [i]

        _logger.info(f'{model} #{id} writen in Odoo db.')
    def write_releves(self, releves: pd.DataFrame)-> List[int]:
        print(releves.columns)
        return [0]
        

