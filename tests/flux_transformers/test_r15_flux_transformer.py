import pytest
from unittest.mock import patch, MagicMock
from pandas.testing import assert_frame_equal
from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer, R15FluxTransformer
import pandas as pd

def test_dict_to_dataframe():
    with patch.object(BaseFluxTransformer, '__init__', return_value=None) as mock_execute:
        transformer = R15FluxTransformer('xsd_path')
    input_data = {
        'PRM': [
            {
                'Id_PRM': 'PRM1',
                'Donnees_Releve': [
                    {
                        'Date_Releve': '2022-01-01',
                        'Classe_Temporelle_Distributeur': [
                            {
                                'Classe_Mesure': '1',
                                'Id_Classe_Temporelle': 'CT1',
                                'Valeur': '100'
                            },
                            {
                                'Classe_Mesure': '2',
                                'Id_Classe_Temporelle': 'CT2',
                                'Valeur': '200'
                            }
                        ]
                    }
                ]
            }
        ]
    }
    expected_columns = pd.MultiIndex.from_tuples([
        ('', 'meta', 'pdl'),
        ('', 'meta', 'Date_Releve'),
        ('index', 'CT1', 'Classe_Mesure'),
        ('index', 'CT1', 'Id_Classe_Temporelle'),
        ('index', 'CT1', 'Valeur'),
        ('conso', 'CT2', 'Classe_Mesure'),
        ('conso', 'CT2', 'Id_Classe_Temporelle'),
        ('conso', 'CT2', 'Valeur'),
    ])
    expected_data = [
        ['PRM1', '2022-01-01', '1', 'CT1', '100', '2', 'CT2', '200']
    ]
    expected_df = pd.DataFrame(expected_data, columns=expected_columns)

    # Exercise
    result_df = transformer.dict_to_dataframe(input_data)

    # Verify
    assert_frame_equal(result_df, expected_df)