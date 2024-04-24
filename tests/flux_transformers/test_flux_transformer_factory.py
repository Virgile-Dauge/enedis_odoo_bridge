import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer, R15FluxTransformer, FluxTransformerFactory

# Assuming the FluxTransformerFactory class is in a module named flux_transformers_factory.py
# from your_project.flux_transformers.flux_transformers_factory import FluxTransformerFactory

@pytest.fixture
def xsd_path():
    return Path("/path/to/xsd")

@pytest.fixture
def transformer_factory():
    return FluxTransformerFactory()

def test_get_transformer_with_supported_flux_type(transformer_factory, xsd_path):
    with patch.object(BaseFluxTransformer, '__init__', return_value=None) as mock_execute:
        transformer = transformer_factory.get_transformer('R15', xsd_path)
        assert isinstance(transformer, R15FluxTransformer), "The returned transformer should be an instance of R15FluxTransformer"
        mock_execute.assert_called_with(xsd_path)

def test_get_transformer_with_unsupported_flux_type(transformer_factory, xsd_path):
    with patch.object(BaseFluxTransformer, '__init__', return_value=None) as mock_execute, pytest.raises(ValueError) as excinfo:
        transformer_factory.get_transformer('UnsupportedType', xsd_path)
    assert "Unsupported Flux type" in str(excinfo.value), "A ValueError should be raised for unsupported flux types"