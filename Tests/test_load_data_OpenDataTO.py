import pytest
import pandas as pd

from annual_police_report import load_data_OpenDataTO

def test_load_data_OpenDataTO():
    package_id = "police-annual-statistical-report-arrested-and-charged-persons"
    result = load_data_OpenDataTO(package_id)
    
    assert result is not None
    assert isinstance(result, pd.DataFrame)