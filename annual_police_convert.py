import nbformat
import yaml

# Load annual_police_report.ipynb
notebook = nbformat.read("annual_police_report.ipynb", as_version=4)

# Converting the notebook to a dictionary (JSON-like structure)
notebook_dict = nbformat.writes(notebook)

# Convert the dictionary to a YAML file
with open("output.yaml", "w") as file:
    yaml.dump(notebook_dict, file)