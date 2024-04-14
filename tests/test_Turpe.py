import pytest

import pandas as pd
from enedis_odoo_bridge.Turpe import Turpe

__author__ = "Virgile"
__copyright__ = "Virgile"
__license__ = "GPL-3.0-only"

@pytest.fixture
def mock_env_turpe(monkeypatch):
    monkeypatch.setenv("TURPE_TAUX_HPH_CU4", '1.0')
    monkeypatch.setenv("TURPE_TAUX_HCH_CU4", '2')
    monkeypatch.setenv("TURPE_TAUX_HPB_CU4", '3')
    monkeypatch.setenv("TURPE_TAUX_HCB_CU4", '4')
    monkeypatch.setenv("TURPE_B_CU4", '5')
    monkeypatch.setenv("TURPE_CG", '6')
    monkeypatch.setenv("TURPE_CC", '7')

@pytest.fixture
def mock_env_missing(monkeypatch):
    monkeypatch.setenv("TURPE_TAUX_HPH_CU4", '')
    #monkeypatch.delitem(Turpe.constants, "TURPE_TAUX_HPH_CU4", raising=False)

def test_init_env_missing(mock_env_missing):
    with pytest.raises(OSError):
        turpe = Turpe()


def test_compute_value_error(mock_env_turpe):
    input_releves = pd.DataFrame({
        'HPH_conso': [1, 2],
        'HCH_conso': [3, 4],
        'HPB_conso': [5, 6],
        'HCB_conso': [7, 8],
    })
    turpe = Turpe()
    with pytest.raises(ValueError):
        turpe.compute(input_releves)

def test_compute(mock_env_turpe):
    # Arrange
    input_releves = pd.DataFrame({
        'HPH_conso': [1, 2],
        'HCH_conso': [3, 4],
        'HPB_conso': [5, 6],
        'HCB_conso': [7, 8],
        'puissance_souscrite': [1, 2]
    })

    # Act
    turpe = Turpe()
    output_releves = turpe.compute(input_releves)

    # Assert
    t1 = (5*1+6+7)/12 + 1*1*0.01 + 2*3*0.01 + 3*5*0.01 + 4*7*0.01
    t2 = (5*2+6+7)/12 + 1*2*0.01 + 2*4*0.01 + 3*6*0.01 + 4*8*0.01
    expected_output_releves = pd.DataFrame({
        'HPH_conso': [1, 2],
        'HCH_conso': [3, 4],
        'HPB_conso': [5, 6],
        'HCB_conso': [7, 8],
        'puissance_souscrite': [1, 2],
        'turpe': [t1, t2]
    })

    pd.testing.assert_frame_equal(output_releves, expected_output_releves)