
import logging
import requests
import pandas as pd
import json

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), logging.FileHandler('package_id')])

def load_data_OpenDataTO(package_id):
    """
    Load a dataset from the Toronto Open Data API.

    Parameters:
    - package_id (str): The ID of the package containing the dataset in a dict {}.

    Returns:
    - pd.DataFrame or None: A DataFrame containing the dataset if successfully loaded, 
                            or None if an error occurred.
    """
    # Define the base URL for the Toronto Open Data API
    base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"

    # Define the URL to access the metadata of a package
    metadata_url = base_url + "/api/3/action/package_show"

    # Set the parameters to retrieve information about the desired package
    params = {"id": package_id}
         
    # Send a GET request to retrieve metadata about the package
    response = requests.get(metadata_url, params=params)

    # Check if the GET request was successful
    if response.status_code == 200:
        # Parse the JSON response
        package_info = response.json()
        
        # Extract information about the resources in the package
        resources = package_info['result']['resources']
        
        # Look for a JSON resource and load its data using CKAN API
        for resource in resources:
            if resource['format'].lower() == 'json':
                data_url = base_url + "/api/3/action/datastore_search"
                params = {"id": resource["id"]}
                filters = {
                    "ARREST_YEAR": [2018, 2019, 2020, 2021, 2022],
                    "DIVISION": "D11"  # Filter for DIVISION
                }

                all_records = []
                limit = 1000  # Number of records to retrieve per request
                
                # Paginate through the data until all records are retrieved
                offset = 0
                while True:
                    params["offset"] = offset
                    params["limit"] = limit
                    params["filters"] = json.dumps(filters)  # Encode filters as JSON string
                    response = requests.get(data_url, params=params)
                    response_json = response.json()
                    if "result" not in response_json or not response_json["success"]:
                        logging.error("Error retrieving data from the API.")
                        return None
                    
                    resource_search_data = response_json["result"]
                    records = resource_search_data.get("records", [])
                    all_records.extend(records)
                    
                    # Check if we have fetched all records
                    if len(records) < limit:
                        break  # Break the loop if all records have been retrieved
                    
                    offset += limit  # Move to the next page
                
                df = pd.DataFrame(all_records)
                logging.info("Toronto Open DataFrame created successfully using CKAN API parameters.")
                return df
        else:
            logging.warning("No JSON resource found in the package.")
            return None
            
    else:
        logging.error("Failed to retrieve metadata from the API.")
        return None

# Load the Annual Police Report data into the DataFrame
    
package_id = "police-annual-statistical-report-arrested-and-charged-persons"

annual_police_report = load_data_OpenDataTO(package_id)
if annual_police_report is not None:
    annual_police_report.head()
else:
    logging.error("Failed to load the dataset.")
annual_police_report.head()

# %%
#converting column names to lowecase
def rename_data(annual_police_report):
  if annual_police_report is None:
    raise ValueError('No columns found')
  report=annual_police_report.rename(columns=str.lower)
  return report
rename_data(annual_police_report)
annual_police_report=rename_data(annual_police_report)
annual_police_report.head()

# %%


# %%


# %%



