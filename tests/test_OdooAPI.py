import pytest
import numpy as np
import pandas as pd
from pandas import DataFrame
from unittest.mock import patch, MagicMock
from enedis_odoo_bridge.OdooAPI import OdooAPI

def test_ensure_connection_calls_connect():
    # Mock the connect method
    with patch.object(OdooAPI, 'get_uid', return_value=42) as mock_connect, patch('xmlrpc.client.ServerProxy') as mock_proxy:
        # Create an instance of OdooAPI with proxy and uid set to None to simulate a disconnected state
        odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)
        odoo_api.proxy = None
        odoo_api.uid = None

        # Mocked execute method 
        odoo_api.execute('some_model', 'some_method')

        # Assert that connect was called
        assert odoo_api.uid == 42
        mock_connect.assert_called_once()

def test_ensure_connection_does_not_call_connect_when_already_connected():
    # Mock the connect method
    with patch.object(OdooAPI, 'connect') as mock_connect, patch.object(OdooAPI, 'execute', return_value=None) as mock_execute:
        # Create an instance of OdooAPI with proxy and uid set to simulate an already established connection
        odoo_api = OdooAPI(config={'URL': '', 'DB': '', 'USERNAME': '', 'PASSWORD': ''}, sim=True)
        odoo_api.proxy = MagicMock()
        odoo_api.uid = 1  # Simulate a valid user ID

        # Directly call the connect method to simulate the behavior of a decorated method
        odoo_api.execute()

        # Assert that connect was not called since the connection is already established
        mock_connect.assert_not_called()
@pytest.fixture
def setup_odoo_api():
    config = {'URL': 'http://example.com', 'DB': 'test_db', 'USERNAME': 'user', 'PASSWORD': 'pass'}
    odoo_api = OdooAPI(config)
    return odoo_api

@pytest.fixture
def setup_odoo_api_for_fetch():
    odoo_api = OdooAPI(config={'URL': 'http://example.com', 'DB': 'test_db', 'USERNAME': 'user', 'PASSWORD': 'pass'}, sim=False)
    odoo_api.get_drafts = MagicMock(return_value=pd.DataFrame({'invoice_line_ids': [[1, 2]], 'date': ['2022-01-01'], 'x_order_id': [123]}))
    odoo_api.add_order_fields = MagicMock(return_value=pd.DataFrame({'invoice_line_ids': [[1, 2]], 'date': ['2022-01-01'], 'x_order_id': [123], 'x_pdl': ['pdl1'], 'x_puissance_souscrite': [10]}))
    odoo_api.add_cat_fields = MagicMock(return_value=pd.DataFrame({'invoice_line_ids': [1, 2], 'date': ['2022-01-01', '2022-01-01'], 'x_order_id': [123, 123], 'x_pdl': ['pdl1', 'pdl1'], 'x_puissance_souscrite': [10, 10], 'cat': ['cat1', 'cat2']}))
    odoo_api.filter_non_energy = MagicMock(return_value=pd.DataFrame({'invoice_line_ids': [1], 'date': ['2022-01-01'], 'x_order_id': [123], 'x_pdl': ['pdl1'], 'x_puissance_souscrite': [10], 'cat': ['cat1']}))
    odoo_api.clear = MagicMock(return_value=pd.DataFrame({'date': ['2022-01-01'], 'x_order_id': [123], 'x_pdl': ['pdl1'], 'x_puissance_souscrite': [10], 'cat': ['cat1']}))
    return odoo_api

def test_fetch(setup_odoo_api_for_fetch):
    expected_df = pd.DataFrame({'date': ['2022-01-01'], 'x_order_id': [123], 'x_pdl': ['pdl1'], 'x_puissance_souscrite': [10], 'cat': ['cat1']})
    result_df = setup_odoo_api_for_fetch.fetch()
    pd.testing.assert_frame_equal(result_df, expected_df)

    setup_odoo_api_for_fetch.get_drafts.assert_called_once()
    setup_odoo_api_for_fetch.add_order_fields.assert_called_once()
    setup_odoo_api_for_fetch.add_cat_fields.assert_called_once()
    setup_odoo_api_for_fetch.filter_non_energy.assert_called_once()
    setup_odoo_api_for_fetch.clear.assert_called_once()

def test_filter_non_energy_things_to_filter(setup_odoo_api):
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
    odoo_api = setup_odoo_api

    # Filter the data
    filtered_data = odoo_api.filter_non_energy(data)

    # Verify that the filtered data matches the expected data
    pd.testing.assert_frame_equal(filtered_data.reset_index(drop=True), expected_data.reset_index(drop=True))

def test_filter_non_energy_nothing_to_filter(setup_odoo_api):
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
    odoo_api = setup_odoo_api

    # Filter the data
    filtered_data = odoo_api.filter_non_energy(data)

    # Verify that the filtered data matches the expected data
    pd.testing.assert_frame_equal(filtered_data.reset_index(drop=True), expected_data.reset_index(drop=True))

def test_clear_removes_non_scalar_columns(setup_odoo_api):
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
    odoo_api = setup_odoo_api

    # Exercise: Use the clear method to remove non-scalar columns
    cleared_data = odoo_api.clear(data)

    # Verify: The returned DataFrame should match the expected DataFrame
    pd.testing.assert_frame_equal(cleared_data, expected_data)

def test_add_order_fields_raises_value_error_when_x_order_id_missing(setup_odoo_api):
    # Instantiate OdooAPI with dummy config
    odoo_api = setup_odoo_api
    
    # Prepare test data without 'x_order_id' column
    test_data = DataFrame({
        'NOT_x_order_id': [[1, 'S00001'], [2, 'S00002']]
    })
    
    # Expect ValueError to be raised due to missing 'x_order_id' column
    with pytest.raises(ValueError) as excinfo:
        odoo_api.add_order_fields(test_data, ['field1', 'field2'])
    
    # Optionally, you can check the exception message
    assert "No x_order_id found in" in str(excinfo.value)
    

def test_add_order_fields(setup_odoo_api):
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
    odoo_api = setup_odoo_api

    # Mock self.execute to return the mock_orders when called with 'sale.order', 'read'
    with patch.object(OdooAPI, 'execute', return_value=mock_orders) as mock_execute:
        # Call add_order_fields
        result_data = odoo_api.add_order_fields(test_data, fields_to_add)

    # Verify that execute was called as expected
    mock_execute.assert_called_once_with('sale.order', 'read', [[1, 2]], {'fields': fields_to_add})

    # Assert that the result_data matches the expected_data
    pd.testing.assert_frame_equal(result_data, expected_data)

def test_add_cat_fields_raises_value_error(setup_odoo_api):
    # Instantiate the OdooAPI class with dummy configuration
    odoo_api = setup_odoo_api
    
    # Create a DataFrame without the 'invoice_line_ids' column
    data = pd.DataFrame({
        'id': [1, 2],
        'some_other_column': ['value1', 'value2']
    })
    
    # Expect ValueError to be raised due to missing 'invoice_line_ids' column
    with pytest.raises(ValueError) as exc_info:
        odoo_api.add_cat_fields(data, [])
    
    # Optionally, check the exception message to ensure it's the expected one
    assert "No invoice_line_ids found in" in str(exc_info.value)

def test_add_cat_fields(setup_odoo_api):
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
    odoo_api = setup_odoo_api

    with patch.object(OdooAPI, 'execute', side_effect=[mock_lines_response, mock_products_response]) as mock_execute:
        # Call add_cat_fields
        result_data = odoo_api.add_cat_fields(data, [])

    # Verify that execute was called correctly
    mock_execute.assert_any_call('account.move.line', 'read', [[10, 20, 30]], {'fields': ['product_id']})
    mock_execute.assert_any_call('product.product', 'read', [[1, 2, 3]], {'fields': ['categ_id']})

    # Assert that the result_data matches the expected_data structure
    pd.testing.assert_frame_equal(result_data.reset_index(drop=True), expected_data.reset_index(drop=True), check_dtype=False)

def test_prepare_account_moves_updates_whitout_compteur(setup_odoo_api):
    # Setup test data
    test_data = pd.DataFrame({
        'id': [1, 2],
        'turpe_fix': [10.0, 20.0],
        'turpe_var': [5.0, 10.0],
    })

    # Expected output
    expected_moves = [
        {'id': 1, 'x_turpe': 15.0,},
        {'id': 2, 'x_turpe': 30.0,}
    ]

    # Instantiate OdooAPI with dummy config
    odoo_api = setup_odoo_api

    # Call the method
    actual_moves = odoo_api.prepare_account_moves_updates(test_data)

    # Convert numpy types to native Python types for comparison
    for move in actual_moves:
        for key, value in move.items():
            if isinstance(value, np.number):
                move[key] = value.item()

    # Assert the result
    assert actual_moves == expected_moves, "The method prepare_account_moves_updates did not return the expected result."
def test_prepare_account_moves_updates(setup_odoo_api):
    # Setup test data
    test_data = pd.DataFrame({
        'id': [1, 2],
        'turpe_fix': [10.0, 20.0],
        'turpe_var': [5.0, 10.0],
        'Type_Compteur': ['TC1', 'TC2']
    })

    # Expected output
    expected_moves = [
        {'id': 1, 'x_turpe': 15.0, 'x_type_compteur': 'TC1'},
        {'id': 2, 'x_turpe': 30.0, 'x_type_compteur': 'TC2'}
    ]

    # Instantiate OdooAPI with dummy config
    odoo_api = setup_odoo_api

    # Call the method
    actual_moves = odoo_api.prepare_account_moves_updates(test_data)

    # Convert numpy types to native Python types for comparison
    for move in actual_moves:
        for key, value in move.items():
            if isinstance(value, np.number):
                move[key] = value.item()

    # Assert the result
    assert actual_moves == expected_moves, "The method prepare_account_moves_updates did not return the expected result."

def test_create_single_entry_returns_single_id(setup_odoo_api):
    single_entry = {'name': 'Test Entry'}
    expected_id = 1  # Assuming the Odoo server returns this ID for the created entry

    with patch.object(OdooAPI, 'execute', return_value=expected_id) as mock_execute:
        result_ids = setup_odoo_api.create('test.model', [single_entry])
        mock_execute.assert_called_once_with('test.model', 'create', [[single_entry]])
        assert result_ids == [expected_id], "The create method should return a list containing the single ID"

def test_create_multiple_entries_returns_multiple_ids(setup_odoo_api):
    entries = [{'name': 'Test Entry 1'}, {'name': 'Test Entry 2'}]
    expected_ids = [1, 2]  # Assuming the Odoo server returns these IDs for the created entries

    with patch.object(OdooAPI, 'execute', return_value=expected_ids) as mock_execute:
        result_ids = setup_odoo_api.create('test.model', entries)
        mock_execute.assert_called_once_with('test.model', 'create', [entries])
        assert result_ids == expected_ids, "The create method should return a list of IDs"
