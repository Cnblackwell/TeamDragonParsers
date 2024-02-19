# Importing libraries and dependencies
import logging
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
class TeamDragonParsers:
    
    def __init__(self, analysis_config):
       logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), logging.FileHandler('package_id_log')])

    def load_data_OpenDataTO(self, package_id_log):
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
        params = {"id": package_id_log}
            
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
                        #"ARREST_YEAR": [2014,2015,2016,2017,2018, 2019, 2020, 2021, 2022],
                        "DIVISION": "D11"  # Filter for DIVISION(Geographic division where crime took place)
                    }

                    all_records = []
                    limit = 5000  # Number of records to retrieve per request
                    
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
    
    def rename_data(self, annual_police_report):
        #converting column names to lowercase
        if annual_police_report is None:
            raise ValueError('No columns found')
        report=annual_police_report.rename(columns=str.lower)
        return report
    
    def total_only_f(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        
        # Create a dataframe where 'category' is Total Arrests only 
        total_data = dataframe[dataframe['category'] == 'Total Arrests']

        return total_data
    def by_year_f(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        # Group rows by year
        by_group = dataframe.groupby(['arrest_year'])

        # Add up all Total Arrests for each year
        year_sum = by_group.agg(arrest_count = ('arrest_count', 'sum'))

        return year_sum
    
    def year_column(self, data: pd.DataFrame,column):
        fig,ax = plt.subplots()
        ax.set_axisbelow(True)
        ax.grid(alpha=0.3)   
        offset=0.7
        count = ax.bar(data.index, data[column], width=offset)
        ax.set_title('(Division-D11) Toronto \n ARRESTS COUNT BY YEAR', fontweight='bold')
        ax.set_xlabel('Year')
        ax.set_ylabel('Counts')
        plt.savefig('arrest_by_year.pdf')
        #plt.clf()  # Clear the current figure
        plt.show()

    def conditions_f(self, row):    
        if row["age_group"] == 'Adult':
            row['_adult'] = row['arrest_count']
            row['_youth'] = 0
        elif row["age_group"] == 'Youth':
            row['_adult'] = 0
            row['_youth'] = row['arrest_count']
        return row[['_adult','_youth']]
    def arrest_by_year(self, data: pd.DataFrame) -> pd.DataFrame:

        # Group rows by year
        year_age_group = data.groupby(['arrest_year','age_group'])

        # Add up all Total Arrests for each year
        year_age_sum = year_age_group.agg(arrest_count = ('arrest_count', 'sum')).reset_index()

        # dropping unknown age_group
        year_age_sum = year_age_sum.drop(year_age_sum[year_age_sum['age_group'] == 'Unknown'].index)  

        # create columns '_adult', '_youth' based on 'age_group
        year_age_sum[['_adult','_youth']] = year_age_sum.apply(self.conditions_f, axis=1)


        # drop 'age_group' and 'arrest_count' because these values have been moved to '_adult','_youth'
        year_age_sum = year_age_sum.drop(['age_group', 'arrest_count'], axis=1)

        # group by year 
        year_age_group = year_age_sum.groupby(['arrest_year']).agg(adult=('_adult','sum'),
                                        youth=('_youth','sum')).reset_index()

        return year_age_group
    def arrest_by_age_year(self, data, years):
        barWidth = 0.35

        # Set the position of the bars on the x-axis
        r1 = np.arange(len(data['adult']))
        r2 = [x + barWidth for x in r1]

        # Create the bar plots
        plt.bar(r1, data['adult'], color='blue', width=barWidth, edgecolor='white', label='Adult')
        plt.bar(r2, data['youth'], color='red', width=barWidth, edgecolor='white', label='Youth')

        # Add x-axis and y-axis labels and a title
        plt.xlabel('Year')
        plt.ylabel('Counts')
        plt.title('(Division-D11) Toronto \n ARRESTS COUNT BY YEAR', fontweight='bold')

        # Add x-axis tick labels for years
        plt.xticks([r + barWidth / 2 for r in range(len(data['adult']))], years)
        
        # Add legend
        plt.legend()
        plt.savefig('arrest_by_year_age.png')
        #plt.clf()  # Clear the current figure
        plt.show()
    
    def arrest_cohort(self, annual_police_report):
        try:
            # Group the data by 'age_cohort' and 'arrest_year' and sum the 'arrest_count' for each group
            grouped_data = annual_police_report.groupby(['age_cohort', 'arrest_year'], observed=True)['arrest_count'].sum()

            # Create a dictionary to store subsets of data for each age cohort
            subset_dict = {}

            # Iterate through each group
            for (age_cohort, arrest_year), total_arrests in grouped_data.items():
                try:
                    # Check if the age cohort already exists in the dictionary
                    if age_cohort not in subset_dict:
                        # If not, create a new entry with an empty list
                        subset_dict[age_cohort] = []

                    # Append the current group to the corresponding age cohort entry
                    subset_dict[age_cohort].append((arrest_year, total_arrests))
                except Exception as e:
                    print(f"An error occurred while processing group: {age_cohort}, {arrest_year}")
                    print(e)

            # Plot each subset
            for age_cohort, subset_data in subset_dict.items():
                plt.plot([data[0] for data in subset_data], [data[1] for data in subset_data], label=age_cohort)

            # Add labels and legend
            plt.xlabel('Year')
            plt.ylabel('Total Arrests')
            plt.title('(Division-D11) Toronto \n ARRESTS COUNT BY YEAR AND AGE COHORT', fontweight='bold')
            plt.legend(title='AGE COHORT', bbox_to_anchor=(1, 1), loc='upper left')
        except Exception as e:
            print("An error occurred during plot generation:")
            print(e)
        plt.savefig('arrest_by_year_age_cohort.pdf')
        #plt.clf()  # Clear the current figure
        plt.show()

    def linear_regression(self, annual_police_report):
        #Show a simple analysis, with mean, max, min for Arrest Year and Arrest Count columns
        analysis_annual_police_report = annual_police_report.describe()

        analysis_annual_police_reportROUNDED = analysis_annual_police_report.round()

        analysis_annual_police_reportROUNDED

        # Use sklearn module to start predicting data and model

        from sklearn.linear_model import LinearRegression

        # Extracting the features (X) and the target variable (y)
        X = annual_police_report[['arrest_year']]
        y = annual_police_report['arrest_count']

        # Initializing the linear regression model
        model = LinearRegression()

        # Fitting the model to your data
        model.fit(X, y)

        # Printing the intercept and coefficients
        print("Intercept:", model.intercept_)
        print("Coefficient:", model.coef_[0])

        # This plotted Model predicts the crime rate using a linear relationship 
            # between number of arrests over time in Toronto from 2014 to 2022.

        # Plotting the data points
        plt.scatter(annual_police_report['arrest_year'], annual_police_report['arrest_count'], color='teal', label='Data Points')

        # Plotting the regression line 
        '''
        Parameters
        X : array-like or sparse matrix, shape (n_samples, n_features)
            Samples.

        Returns
        C : array, shape (n_samples,)
            Returns predicted values.
        '''
        plt.plot(annual_police_report['arrest_year'], model.predict(annual_police_report[['arrest_year']]), color='orange', label='Regression Line')

        # Adding labels and title
        plt.xlabel('Year')
        plt.ylabel('Number of Arrests')
        plt.title('Linear Regression: "Number of Arrests over Time"')
        plt.legend()
        plt.savefig('Linear_regression.pdf')
        plt.show()
    
if __name__ == "__main__":
    analysis_config = ""  # You need to define this variable
    instance_class = TeamDragonParsers(analysis_config)

    package_id = "police-annual-statistical-report-arrested-and-charged-persons"
    annual_police_report = instance_class.load_data_OpenDataTO(package_id)

    if annual_police_report is not None:
        annual_police_report.head()
    else:
        logging.error("Failed to load the dataset.")

    instance_class.rename_data(annual_police_report)
    annual_police_report = instance_class.rename_data(annual_police_report)

    total_df = instance_class.total_only_f(annual_police_report)
    by_year = instance_class.by_year_f(total_df)

    instance_class.year_column(by_year, 'arrest_count')
    

    year_age_df = instance_class.arrest_by_year(total_df)
    arrest_year = year_age_df['arrest_year']

    instance_class.arrest_by_age_year(year_age_df, arrest_year)

    instance_class.arrest_cohort(annual_police_report)

    instance_class.linear_regression(annual_police_report)
    ####### END ####

 def __init__(self, analysis_config):
       logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), logging.FileHandler('package_id_log')])
 
def hello_world():
    print("Hello, world!")

def cool_beans(self, annual_police_report):
        #Show a simple analysis, with mean, max, min for Arrest Year and Arrest Count columns
        analysis_annual_police_report = annual_police_report.describe()

        analysis_annual_police_reportROUNDED = analysis_annual_police_report.round()

        analysis_annual_police_reportROUNDED

        # Use sklearn module to start predicting data and model

        from sklearn.linear_model import LinearRegression

        # Extracting the features (X) and the target variable (y)
        X = annual_police_report[['arrest_year']]
        y = annual_police_report['arrest_count']

        # Initializing the linear regression model
        model = LinearRegression()

        # Fitting the model to your data
        model.fit(X, y)

        # Printing the intercept and coefficients
        print("Intercept:", model.intercept_)
        print("Coefficient:", model.coef_[0])

        # This plotted Model predicts the crime rate using a linear relationship 
            # between number of arrests over time in Toronto from 2014 to 2022.

        # Plotting the data points
        plt.scatter(annual_police_report['arrest_year'], annual_police_report['arrest_count'], color='teal', label='Data Points')

        # Plotting the regression line 
        '''
        Parameters
        X : array-like or sparse matrix, shape (n_samples, n_features)
            Samples.

        Returns
        C : array, shape (n_samples,)
            Returns predicted values.
        '''
        plt.plot(annual_police_report['arrest_year'], model.predict(annual_police_report[['arrest_year']]), color='orange', label='Regression Line')

        # Adding labels and title
        plt.xlabel('Year')
        plt.ylabel('Number of Arrests')
        plt.title('Linear Regression: "Number of Arrests over Time"')
        plt.legend()
        plt.savefig('Linear_regression.pdf')
        plt.show()