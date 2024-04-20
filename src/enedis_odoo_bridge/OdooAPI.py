import xmlrpc.client
from xmlrpc.client import MultiCall
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Hashable, Tuple
import pandas as pd
from pandas import DataFrame
from datetime import date

from enedis_odoo_bridge.utils import check_required

import logging
_logger = logging.getLogger(__name__)

def ensure_connection(func):
    def wrapper(self, *args, **kwargs):
        if self.proxy is None or self.uid is None:
            self.connect()
        return func(self, *args, **kwargs)
    return wrapper

class OdooAPI:
    def __init__(self, config: Dict[str, str], sim=False):

        self.config = check_required(config, ['URL', 'DB', 'USERNAME', 'PASSWORD'])
        self.url = config['URL']
        db = config['DB']
        self.db = db + '-duplicate' if sim else db
        self.username = config['USERNAME']
        self.password = config['PASSWORD']

        self.uid = None
        self.proxy = None

    def connect(self):
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
    @ensure_connection
    def execute(self, model: str, method: str, args=None, kwargs=None) -> List:
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
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
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
        data = self.filter_non_energy(data)
        return self.clear(data)

    def filter_non_energy(self, data: DataFrame) -> DataFrame:
        """
        Filters out rows from the DataFrame that do not have any energy consumption data.

        This method checks for the presence of non-null values in the columns that represent energy consumption
        ('line_id_Base', 'line_id_HP', 'line_id_HC'). If a row does not have any non-null values in these columns,
        it is considered to not have energy consumption data and is filtered out.

        Args:
            data (DataFrame): The input DataFrame containing invoice line items.

        Returns:
            DataFrame: A DataFrame with rows that lack energy consumption data removed.

        Note:
            The method specifically looks for the presence of 'line_id_Base', 'line_id_HP', and 'line_id_HC' columns
            to determine if the invoice is related to energy consumption. 
            Rows are kept if they have at least one non-null value in any of these columns.
        """
        to_check = [k for k in ['line_id_Base', 'line_id_HP', 'line_id_HC'] if k in data.columns]
        return data.dropna(subset=to_check, how='all')
      
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

    def prepare_line_updates(self, data:DataFrame)-> List[Dict[Hashable, Any]]:
        if 'Base' not in data.columns:
            raise ValueError(f'Required "Base" column found in {data.columns}')
        if 'line_id_Abonnements' not in data.columns:
            raise ValueError(f'Required "line_id_Abonnements" column found in {data.columns}')

        # Get cols names containing line id for consumptions only
        line_id_cols = sorted([c for c in data.columns
                        if c.startswith('line_id_') 
                        and c.replace('line_id_', '') in ['HP', 'HC', 'Base']])
        value_cols = sorted([c for c in data.columns
                      if c in ['HP', 'HC', 'Base']])
        consumption_lines = pd.DataFrame({
            'id': pd.concat([data[c] for c in line_id_cols], ignore_index=True),
            'quantity': pd.concat([data[c] for c in value_cols], ignore_index=True)
        })
        consumption_lines = consumption_lines.dropna(subset=['id']).to_dict(orient='records')

        # Abonnements
        data['days'] = (data['end_date']-data['start_date']).dt.days+1
        subscription_lines = data[['line_id_Abonnements','days']].copy()

        subscription_lines['start_date'] = data['start_date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        subscription_lines['end_date'] = data['end_date'].dt.strftime('%Y-%m-%dT%H:%M:%S')

        names = self.execute('account.move.line', 'read', [data['line_id_Abonnements'].to_list()],
                             {'fields': ['name']})

        subscription_lines['name'] = [n['name'].split('-')[0] for n in names]
        subscription_lines = subscription_lines.rename(columns={'line_id_Abonnements': 'id', 
                                                                'days': 'quantity',
                                                                'start_date': 'deferred_start_date',
                                                                'end_date': 'deferred_end_date',}).to_dict(orient='records')
        return consumption_lines + subscription_lines
  
    def prepare_account_moves_updates(self, data:DataFrame)-> List[Dict[Hashable, Any]]:
        # On veut ajouter x_type_compteur, x_scripted, x_turpe

        moves = DataFrame(data['id'])
        moves['x_turpe'] = data['turpe_fix'] + data['turpe_var']
        # Deprecated : Maintenant on a les activités
        #moves['x_scripted'] = True
        if 'Type_Compteur' in data.columns:
            moves['x_type_compteur'] = data['Type_Compteur']
        return moves.to_dict(orient='records')

    def update_draft_invoices(self, data: DataFrame, start: date, end: date)-> None:
        """
        Updates the draft invoices in the Odoo database.

        Args:
            data (DataFrame): The input data frame.

        Returns:
            None: None.

        This function updates the draft invoices in the Odoo database.
        """
        lines = self.prepare_line_updates(data)
        self.update('account.move.line', lines)
        moves = self.prepare_account_moves_updates(data)
        self.update('account.move', moves)
        _logger.info(f'Draft invoices updated in {self.url} db.')
        self.ask_for_approval('account.move', data['id'].to_list())

    def write(self, model: str, entries: List[Dict[Hashable, Any]])-> List[int]:
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

    def update(self, model: str, entries: List[Dict[Hashable, Any]])-> None:
        id = []
        for e in entries:
            i = int(e['id'])
            del e['id']
            data = e
            data = {k: int(v) if type(v) is np.int64 else v for k, v in data.items()}
            data = {k: float(v) if type(v) is np.int64 else v for k, v in data.items()}
            self.execute(model, 'write', [[i], data])
            id += [i]

        _logger.info(f'{model} #{id} writen in Odoo db.')
      
    def ask_for_approval(self, model: str, ids: List[int]):
        model_id = self.execute('ir.model', 'search', [[['model', '=', model]]])
        activities = DataFrame({'res_id': ids})
        activities['res_model_id'] = model_id[0]
        activities['activity_type_id'] = 4
        activities['user_id'] = self.config['ODOO_FACTURISTE_ID']
        activities['summary'] = 'À Approuver'
        activities['automated'] = True
        activities['note'] = 'Merci de valider cette facture remplie automatiquement.'
        activities['date_deadline'] = date.today().replace(day=5).strftime('%Y-%m-%d')
        self.execute('mail.activity', 'create', [activities.to_dict(orient='records')])

