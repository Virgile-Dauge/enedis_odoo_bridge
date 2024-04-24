
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import zipfile
from pandas import DataFrame, Timestamp
from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer  # Adjust the import path according to your project structure
from unittest.mock import patch

# Step 1: Create a Concrete Subclass for Testing
class ConcreteFluxTransformer(BaseFluxTransformer):
    def dict_to_dataframe(self, data_dict):
        # Implement abstract method
        df = DataFrame(data_dict)
        return df
    def preprocess(self):
        pass

@pytest.fixture
def setup_test_files():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir_path = Path(tmpdirname)  # Convert to Path object for easier manipulation

        # Create an XSD file in the temporary directory
        xsd_path = tmpdir_path / "schema.xsd"
        xsd_path.write_text('''<?xml version="1.0" encoding="utf-8"?>
                            <xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
                            <xs:element name="root">
                                <xs:complexType>
                                <xs:sequence>
                                    <xs:element maxOccurs="unbounded" name="date" type="xs:dateTime" />
                                </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                            </xs:schema>
                            ''')
        # Create an XML file in the temporary directory
        xml_path = tmpdir_path / "test.xml"
        xml_path.write_text("<root><date>2021-01-01T00:00:00+02:00</date><date>2021-01-01T00:00:00+02:00</date></root>")
        
        zip_path = tmpdir_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(xml_path, arcname=xml_path.name)

        yield xsd_path, zip_path


def test_process_zip_FileNotFound(setup_test_files):
    xsd_path, zip_path = setup_test_files
    transformer = ConcreteFluxTransformer(xsd_path)
    with pytest.raises(FileNotFoundError):
        transformer.process_zip(zip_path / 'nonono')




def test_process_zip_success(setup_test_files):
    xsd_path, zip_path = setup_test_files
    transformer = ConcreteFluxTransformer(xsd_path)
    result_df = transformer.process_zip(zip_path)
    assert not result_df.empty
    print(result_df)
    assert result_df.iloc[0]['date'] == '2021-01-01T00:00:00+02:00' #.tz_localize('UTC+2')