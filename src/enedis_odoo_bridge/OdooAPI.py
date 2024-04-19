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
        _logger.info(f'Logged to {self.db} Odoo db.')

    def get_uid(self):
        """
        Authenticates the user with the provided credentials and returns the user ID.

        Args:
            self (OdooAPI): An instance of the OdooAPI class.

        Returns:
            int: The user ID obtained from the Odoo server.

        Raises:
            xmlrpc.client.Fault: If the authentication fails.

        This function creates a ServerProxy object to the Odoo server's XML-RPC interface,
        and calls the 'authenticate' method to authenticate the user with the provided credentials. 
        The user ID obtained from the Odoo server is then returned.
        """
        common_proxy = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        return common_proxy.authenticate(self.db, self.username, self.password, {})
    
    def execute(self, model: str, method: str, args, kwargs) -> List:
        """
        Executes a method on the Odoo server.

        Args:
            model (str): The model to execute the method on.
            method (str): The method to execute.
            *args: Additional positional arguments to pass to the method.
            **kwargs: Additional keyword arguments to pass to the method.

        Returns:
            List: The result of the executed method, if it returns a list. Otherwise, a single value is wrapped in a list.

        Raises:
            xmlrpc.client.Fault: If the execution fails.

        This function creates a ServerProxy object to the Odoo server's XML-RPC interface,
        and calls the 'execute_kw' method to execute the specified method on the specified model.
        The result of the executed method is then returned, wrapped in a list if it is a single value.
        """
        _logger.debug(f'Executing {method} on {model} with args {args} and kwargs {kwargs}')
        res = self.proxy.execute_kw(self.db, self.uid, self.password, model, method, args, kwargs)
        return res if isinstance(res, list) else [res]
    
    def fetch(self) -> DataFrame:
        """
        Fetches draft invoices from Odoo db, enrich them with data form sale.order and account.move.lines data.

        Args:
            self (OdooAPI): An instance of the OdooAPI class.

        Returns:
            DataFrame: A DataFrame containing the draft invoices with the specified fields.

        This function first fetches ['invoice_line_ids', 'date', 'x_order_id'] fields of draft invoices.
        It then adds ['x_pdl', 'x_puissance_souscrite'] fields from the 'sale.order'.
        Finally, it adds one category column to the data frame for each invoice line, set with the corresponding line id.
        The function returns the cleared DataFrame, leaving only scalar values.
        """
        data = self.get_drafts(['invoice_line_ids', 'date', 'x_order_id'])
        data = self.add_order_fields(data, ['x_pdl', 'x_puissance_souscrite'])
        data = self.add_cat_fields(data, [])
        return self.clear(data)
    
    def clear(self, data: DataFrame)-> DataFrame:
        """
        Removes non-scalar columns from the input DataFrame.

        Args:
            data (DataFrame): The input DataFrame to be cleaned.

        Returns:
            DataFrame: The input DataFrame with non-scalar columns removed.

        This function identifies non-scalar columns in the input DataFrame and removes them.
        Non-scalar columns are those that contain lists or dictionaries.
        """
        non_scalar_columns = [col for col in data.columns if any(data[col].apply(lambda x: isinstance(x, (list, dict))))]
        return data.drop(non_scalar_columns, axis=1)

    def get_drafts(self, fields: List[str])-> DataFrame:
        """
        Searches for draft invoices in the specified Odoo database and returns them as a DataFrame.

        Args:
            fields (List[str]): A list of fields to be included in the returned DataFrame.

        Returns:
            DataFrame: A DataFrame containing the draft invoices with the specified fields.

        This function searches for draft invoices in the specified Odoo database and returns them as a DataFrame.
        Draft invoices satisfies : ['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]
        It uses the 'search_read' method to retrieve the draft invoices and includes the specified fields in the returned DataFrame.
        """
        _logger.info(f'Searching drafts invoices in {self.url} db.')
        drafts = self.execute('account.move', 'search_read', 
            [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]]], 
            {'fields': fields})
        return DataFrame(drafts)

    def add_order_fields(self, data: DataFrame, fields: List[str])-> DataFrame:
        """
        Adds the specified fields from the 'sale.order' model to the input DataFrame based on the 'x_order_id' column.

        Args:
            data (DataFrame): The input DataFrame to be updated.
            fields (List[str]): A list of fields to be added from the 'sale.order' model.

        Returns:
            DataFrame: The input DataFrame with the specified fields added.

        Raises:
            ValueError: If the input DataFrame does not have the 'x_order_id' column.

        This function first checks if the input DataFrame has the 'x_order_id' column. 
        If it does, it fetches the corresponding orders from the 'sale.order' model using the 'read' method of the Odoo API. 
        It then creates a new DataFrame from the fetched orders and adds the specified fields to the input DataFrame. 
        Finally, it returns the updated DataFrame.
        """
        if 'x_order_id' not in data.columns:
            raise ValueError(f'No x_order_id found in {data.columns}')
        
        orders = self.execute('sale.order', 'read', 
                            [[d[0] for d in data['x_order_id'].to_list()]], 
                            {'fields': fields})
        df = DataFrame(orders)
        data[fields] = df[fields]
        return data
           
    def add_cat_fields(self, data: DataFrame, fields: List[str])-> DataFrame:
        """
        Add one category column to the data frame for each invoice line, set with the corresponding line id.

        Args:
            data (DataFrame): The input data frame.
            fields (List[str]): The list of category fields to add.

        Returns:
            DataFrame: The input data frame with the added category fields.

        Raises:
            ValueError: If the input data frame does not have the required columns.

        After checking that the input data frame has the required columns,
        Then fetchs the lines of each invoice with invoice_line_ids key.
        Then fetchs the product of each line with product_id key found for each line.
        Then explodes each invoice line into a separate row.
        Then adds the cat columns from the fetcheds products.
        We now have all the data, but we need to return to one row for each invoice.
        We can do this by pivoting the data, and then merging the pivoted data with the original data frame.
        """
        if 'invoice_line_ids' not in data.columns:
            raise ValueError(f'No invoice_line_ids found in {data.columns}')

        df_exploded = data.explode('invoice_line_ids')
        lines = self.execute('account.move.line', 'read', [df_exploded['invoice_line_ids'].to_list()],
                             {'fields': ['product_id']})
        
        prods_id = [l['product_id'][0] if l['product_id'] else False for l in lines]

        prods = self.execute('product.product', 'read', [prods_id],
                        {'fields': ['categ_id']})
        cat = [p['categ_id'][1].split(' ')[-1] for p in prods]
        
        df_exploded['cat'] = cat

        # Pivoting to transform 'cat' values into separate columns
        df_pivoted = df_exploded.pivot(index='id', columns='cat', values='invoice_line_ids').reset_index()
        # Renaming columns to reflect the source of the data
        df_pivoted.columns = ['id'] + [f'line_id_{x}' for x in df_pivoted.columns if x != 'id']

        # Merge the pivoted DataFrame with the original DataFrame
        df_final = pd.merge(data, df_pivoted, on='id', how='left')
        return df_final

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
      

