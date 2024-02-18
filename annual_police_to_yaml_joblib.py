#we will serialize the python code (annual police report) with joblib
from joblib import dump
annual_police_report = {
    'key1': 'value1',
    'key2': 'value2'
}
dump(annual_police_report, 'serialized_annual_police_report.joblib')