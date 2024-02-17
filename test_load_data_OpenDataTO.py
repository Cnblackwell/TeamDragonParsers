import pytest
from my_module import load_data_OpenDataTO

def test_load_data_OpenDataTO():
    package_id = "your_package_id_here"
    result = load_data_OpenDataTO(package_id)
    
    assert result is not None
    assert isinstance(result, pd.DataFrame)