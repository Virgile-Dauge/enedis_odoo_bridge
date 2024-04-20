import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from enedis_odoo_bridge.OdooAPI import OdooAPI

def test_filter_non_energy_things_to_filter():
    # Create a sample DataFrame that includes both energy and non-energy consumption data
    data = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'line_id_Base': [10, None, 20, None],
        'line_id_HP': [None, 30, None, None],
        'line_id_HC': [None, None, None, None],
        'other_column': ['value1', 'value2', 'value3', 'value4']
    })

    # Expected DataFrame after filtering
    expected_data = pd.DataFrame({
        'id': [1, 2, 3],
        'line_id_Base': [10, None, 20],
        'line_id_HP': [None, 30, None],
        'line_id_HC': [None, None, None],
        'other_column': ['value1', 'value2', 'value3']
    })

    # Instantiate the OdooAPI class
    odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)

    # Filter the data
    filtered_data = odoo_api.filter_non_energy(data)

    # Verify that the filtered data matches the expected data
    pd.testing.assert_frame_equal(filtered_data.reset_index(drop=True), expected_data.reset_index(drop=True))

def test_filter_non_energy_nothing_to_filter():
    # Create a sample DataFrame that includes both energy and non-energy consumption data
    data = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'line_id_Base': [10, None, 20, None],
        'line_id_HP': [None, 30, None, None],
        'line_id_HC': [None, None, None, 1],
        'other_column': ['value1', 'value2', 'value3', 'value4']
    })

    # Expected DataFrame after filtering
    expected_data = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'line_id_Base': [10, None, 20, None],
        'line_id_HP': [None, 30, None, None],
        'line_id_HC': [None, None, None, 1],
        'other_column': ['value1', 'value2', 'value3', 'value4']
    })

    # Instantiate the OdooAPI class
    odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)

    # Filter the data
    filtered_data = odoo_api.filter_non_energy(data)

    # Verify that the filtered data matches the expected data
    pd.testing.assert_frame_equal(filtered_data.reset_index(drop=True), expected_data.reset_index(drop=True))

def test_clear_removes_non_scalar_columns():
    # Setup: Create a DataFrame with scalar and non-scalar columns
    data = pd.DataFrame({
        'scalar1': [1, 2, 3],
        'scalar2': ['a', 'b', 'c'],
        'non_scalar_list': [[1, 2], [3, 4], [5, 6]],
        'non_scalar_dict': [{'a': 1}, {'b': 2}, {'c': 3}]
    })

    # Expected DataFrame after clearing non-scalar columns
    expected_data = pd.DataFrame({
        'scalar1': [1, 2, 3],
        'scalar2': ['a', 'b', 'c']
    })

    # Instantiate OdooAPI with dummy config
    odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)

    # Exercise: Use the clear method to remove non-scalar columns
    cleared_data = odoo_api.clear(data)

    # Verify: The returned DataFrame should match the expected DataFrame
    pd.testing.assert_frame_equal(cleared_data, expected_data)

def test_add_order_fields():
    # Prepare test data
    test_data = pd.DataFrame({
        'x_order_id': [[1, 'S00001'], [2, 'S00002']]
    })
    fields_to_add = ['field1', 'field2']
    mock_orders = [
        {'id': 1, 'field1': 'value1_1', 'field2': 'value2_1'},
        {'id': 2, 'field1': 'value1_2', 'field2': 'value2_2'}
    ]

    # Expected DataFrame after adding order fields
    expected_data = pd.DataFrame({
        'x_order_id': [[1, 'S00001'], [2, 'S00002']],
        'field1': ['value1_1', 'value1_2'],
        'field2': ['value2_1', 'value2_2']
    })

    # Instantiate OdooAPI with dummy config
    odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)

    # Mock self.execute to return the mock_orders when called with 'sale.order', 'read'
    with patch.object(OdooAPI, 'execute', return_value=mock_orders) as mock_execute:
        # Call add_order_fields
        result_data = odoo_api.add_order_fields(test_data, fields_to_add)

    # Verify that execute was called as expected
    mock_execute.assert_called_once_with('sale.order', 'read', [[1, 2]], {'fields': fields_to_add})

    # Assert that the result_data matches the expected_data
    pd.testing.assert_frame_equal(result_data, expected_data)

def test_add_cat_fields():
    # Sample input DataFrame
    data = pd.DataFrame({
        'id': [1, 2],
        'invoice_line_ids': [[10, 20], [30]]
    })

    # Expected output DataFrame structure after adding category fields
    expected_data = pd.DataFrame({
        'id': [1, 2],
        'invoice_line_ids': [[10, 20], [30]],
        'line_id_CAT1': [10, None],
        'line_id_CAT2': [20, None],
        'line_id_CAT3': [None, 30]
    })

    # Mock responses for self.execute calls
    mock_lines_response = [{'product_id': [1, 'P1']}, {'product_id': [2, 'P2']}, {'product_id': [3, 'P3']}]
    mock_products_response = [{'categ_id': [1, 'CAT1']}, {'categ_id': [2, 'CAT2']}, {'categ_id': [3, 'CAT3']}]

    # Instantiate OdooAPI with dummy config
    odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)

    with patch.object(OdooAPI, 'execute', side_effect=[mock_lines_response, mock_products_response]) as mock_execute:
        # Call add_cat_fields
        result_data = odoo_api.add_cat_fields(data, [])

    # Verify that execute was called correctly
    mock_execute.assert_any_call('account.move.line', 'read', [[10, 20, 30]], {'fields': ['product_id']})
    mock_execute.assert_any_call('product.product', 'read', [[1, 2, 3]], {'fields': ['categ_id']})

    # Assert that the result_data matches the expected_data structure
    pd.testing.assert_frame_equal(result_data.reset_index(drop=True), expected_data.reset_index(drop=True), check_dtype=False)