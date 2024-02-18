import joblib
import yaml

# Load the serialized file
serialized_data = joblib.load('serialized_annual_police_report.joblib')

# Converting the serialized data to a YAML file
with open('output.yaml', 'w') as file:
    yaml.dump(serialized_data, file)