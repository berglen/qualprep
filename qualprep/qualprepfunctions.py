
# Import libraries
import pandas as pd
import numpy as np 
from tqdm import tqdm
import ast
import math

# Splitting a categorical variable
def split_categorical_vars(series, values_and_labels): 
    '''
    This function splits a variable that comes in list form into multiple variables as 
    specified in the instructions. 
    
    Parameters
    ----------- 
        data: pd series
            Series made up of lists
            
        variable_name: str
            Name of the variable
            
        values_and_labels: dict
            Dictionary of values and labels that specifies the sub-variables to 
            be created (value) and the respective values (keys). For example: for activities the
            dictionary could be {'1': 'eating', '2': 'sleeping', '3': 'fyling', '4': 'fighting'}. 
    Returns
    -------
        pd df
        Splitted variable as df. Column names are values of values_and_labels. Entires are 0 and 1 with
        1 indicating that the repective category was in the list and 0 otherwise. 
    '''
    
    series = series.copy()
    
    output = []
    
    # Go through all responses
    for ind, val in series.items(): 
        
        # Create an empty np array to add categories
        add = np.full(len(values_and_labels), 0)
        
        # Check if the value is empty (no category)
        if not is_nan(val): 
            
            # Split the object if necessary
            if response_length(val) > 1: 
                val = list(val.split(","))
            else: 
                val = [str(val)]
         
            for key in list(values_and_labels.keys()): 

                # If the value is in the series item (i.e., response), add a 1 at the respective place in the add array. 
                
                if key in val: 
                    add[list(values_and_labels.keys()).index(key)] = 1
        
        # Once we checked all keys, add the array to our output
        output.append(add)
    
    # Turn into pd df
    output = pd.DataFrame(output, columns = list(values_and_labels.values()))
    
    return output

# Splitting multiple categorical variables (extension of split_categorical_vars)
def split_multiple_categorical_vars (data, split_info):
    '''
    Function to split multiple variables as indicated in the split_info.
    
    Parameters 
    ----------
        data: pd df
            Dataset containing the variables to be split. 
            
        split_info: pd df
            Instructions on the split. This needs to be a pd df with the two columns
            variable_name and values_and_labels. variable_name contains the variables to be splitted. 
            values_and_labels contains details on possible values and their labels (see split_categorical_vars)
            for more detail. 
    
    Returns
    -------
        pd df
        A dataset with the values splitted according to split_info. The original variables are replaced
        with the splitted version. The names of the new variables correspond to the labels as defined in 
        split_info. The variables are 0 if the respective value was not present and 1 if it was present. 
    '''
    dat = data.copy()
    
    split_info.columns = ["variable_name", "values_and_labels"]
    
    for ind in tqdm(split_info.index): 
        split_variable = split_categorical_vars(dat[split_info.loc[ind, "variable_name"]], 
                                          ast.literal_eval(split_info.loc[ind, "values_and_labels"]))
        dat = dat.drop(columns = split_info.loc[ind, "variable_name"])
        dat = pd.concat([dat, split_variable], axis = 1)
        
    return dat

# Function to create "lookup" for normalization
def get_lookup(df): 
    ''' 
    Get a lookup as pd.df for normalization. 
    
    Paramters
    ---------
        df: pd df
            Normalization file inlcuding "rawstring", "replacement_1" ... "replacement_10"
    
    Returns
    -------
    A look-up (pd.df) with columns as follows: "rawstring", "normalized"
        
    Note: The function ignores capitalization. It will retrun the lookup in all
    low caps. 
    '''
    norm_dict = []
    df_rawstring_index = df.copy()
    df_rawstring_index.rename(columns={df_rawstring_index.columns[0]: "rawstring"}, inplace = True)
    
    # Remove duplicates from the lookup to prevent wrong multiplication
    df_rawstring_index["rawstring"] = df_rawstring_index["rawstring"].str.lower()
    df_rawstring_index.drop_duplicates(subset=['rawstring'], inplace = True)
    
    df_rawstring_index = df_rawstring_index.set_index("rawstring")
    for index, row in df_rawstring_index.iterrows():
        for i in range(0, len(row)):
            if pd.notnull(row[i]):
                norm_dict.append([str(index).lower(), row[i]])
    return pd.DataFrame(norm_dict, columns = ["rawstring", "normalized"])

# Function to replace items under consideration that multiple replacements are possible
    # Used in the normalize_data function
def replace(replace_in_object, replacement_string, position):
    ''' 
    Function to replace an object in a series with multiplying the object if there are multiple replacements. 
    
    Parameters
    ----------
        replace_in_object: pd series
            The object where something has to be replaced (i.e., row of bird sights including 
        'Vermillion and Ghila', 'Arizona', 'eating and sleeping')
            
        replacement_string: list
            List of instances that serve as replacement (e.g., normalized strings for a raw string
                                                         such as "Vermillion fly catcher" and "Ghila woodpecker" for "Vermillion and Ghila") 
        
        position: int
            The position in the replace_in_object where the replacement has to take place 
            (as number, i.e., 0)
        
    Returns
    -------
    List of objects where the replacement have been done. 
    '''
    
    replaced = []
    
    for replstr in replacement_string: 
        
        replace_in_object_copy = replace_in_object.copy()
        replace_in_object_copy[position] = replstr

        replaced.append(replace_in_object_copy)

    return replaced

# Function to normalize datas
def normalize_data(data, lookup, normalization_variable):
    ''' 
    Function to normalize data. 
    
    Parameters
    ----------
    
        data: pd df
            Data to be normalized
            
        lookup: pd df
            Lookup with the rawstring as key and normalized as value. 
            This is the file created by get_lookup. 
        
        normalization_variable: str
            The variable in data that is to be normalized. 
        
    Return: 
        normalized version of data. If an organization raw string contains multiple normalized orgs the
        respective row is copied. 
        
    Note: The function ignores capitalization, it transfers everything into low caps. 
    '''
    normalized_data = []
    problem = []
    
    
    # data = data.reset_index()
    # print(data.index)
    for ind in tqdm(data.index): 
        
        # print(ind)
        # print(data.loc[ind, normalization_variable])
        replacement_string = lookup.loc[lookup["rawstring"] == data.loc[ind, normalization_variable].lower()
        , "normalized"]
        
        if len(replacement_string) == 0: 
            # problem.append([ind, data.loc[ind, normalization_variable]])
            print("No entry found for " + str(data.loc[ind, normalization_variable]) + " in normalization_info. Keep original version." )
        else: 
            normalization_position = data.columns.get_loc(normalization_variable)
            normalized_row = (replace(data.loc[ind], replacement_string, normalization_position))
            [normalized_data.append(entry) for entry in normalized_row]
            # print(normalization_position)
            # print(normalized_data)
    
    normalized_data = pd.DataFrame(normalized_data, columns = data.columns)
    
    return normalized_data

# Replace the normalized strings with the aaggregation strings
def repl_with_agg_string(data, column, replacement_string_dict): 
    '''
    Function to replace the normalized strings with higher-level aggregations strings. 
    
    Parameters
    ----------
        data: pd df
            Data containing the normalized strings that need to be replaced. 
        
        column: str
            Column which contains the normalized strings. 
        
        replacement_string_dict: dict
            Dictionary containing the normalized strings and the 
            higher-level replacement strings. This needs to be in dictionary format. 
            Normalized string as key, higher-level aggregation version as value. 
            For example: "Acorn woodpecker" and "Ghila woodpecker" are replace with "woodpecker"
            {"Acorn woodpecker": "woodpecker", "Ghila woodpecker": "woodpecker"}
        
    Returns
    -------
        pd df    
        Data with normalized strings replaced by higher-level aggregation strings. 
    '''
    
    data_updated = data.copy()
    data_updated = data_updated.reset_index(drop=True)
    
    for ind in data_updated.index: 
        
        data_updated.loc[ind, column] = replacement_string_dict[data_updated.loc[ind, column]]
        
    return data_updated

# Aggregate a column given a particular aggregation function
def aggregate_col(data, aggregation_column, column_to_be_aggregated, agg_function): 
    '''
    Function to aggregate along a column using the agg_function. 
    
    Parameters
    ----------
    
        data: pd df
            Dataset containing the column to be aggregated
        
        aggregation_column: str
            The column along which the data needs to be aggregated. (e.g., species)
        
        column_to_be_aggregated: str
            The column to aggregate. (e.g., weight)
        
        agg_function: str
            The function to use for aggregation. For example, should it be the mean or max. 
            Currently implemented are mean, median, max, min, and one to six. One to six aggregate into 
            1 if the respective number is present and into 0 otherwise. NaNs are ignored.  
    
    Returns
    -------
        pd df
        Aggregated column with aggregation_column as index. This comes as pd df. (e.g., average weight by species)
    '''
    
    if agg_function == "mean": 
        agg_function = custom_mean
        
    if agg_function == "median": 
        agg_function = custom_median
        
    if agg_function == "max": 
        agg_function = custom_max
    
    if agg_function == "min": 
        agg_function = custom_min
        
    if agg_function == "one":
        agg_function = custom_one
        
    if agg_function == "two":
        agg_function = custom_two
        
    if agg_function == "three":
        agg_function = custom_three
        
    if agg_function == "four":
        agg_function = custom_four
        
    if agg_function == "five":
        agg_function = custom_five
        
    if agg_function == "six":
        agg_function = custom_six
    
    agg_col = pd.DataFrame(data.groupby(aggregation_column)[column_to_be_aggregated].agg(agg_function)) # (

    return agg_col


# Aggregate columns according to predefined task list
def aggregate_data(data, aggregation_information, aggregation_variable):
    '''
    Function to aggregate multiple columns as defined in the aggregation_information file. 
    
    Parameters
    ----------
        
        data: pd df
            Data containing the columns to be aggregated. 
        
        aggregation_information: pd df
            Instructions for aggregation. This is a pd df with the two columns
            variable and agg_function. variable contains the variables that need to be aggregated (e.g., weight). 
            agg_function specified the function to be applied for aggreation (e.g., mean). Currently implemented are
            mean, median, max, min, dummy, and one to six. One to six aggregate into 1 if the respective number
            is present and into 0 otherwise. Dummy creates dummy variables first and then aggregates using the 
            "max" function. NaNs are ignored. 
    
    Returns
    -------
        pd df
        A dataset containing all the variables specified in the aggregation_information aggregated according
        to the instructions in the respective dataset. 
    '''
    
    # Replace aggregation_variable with aggregation string
    dat = data.copy()
    
    # Rename the aggregation_information file
    aggregation_information.columns = ["variable", "agg_function"]
    
    # Check if any dummies are requested
    dummies = list(aggregation_information.loc[aggregation_information["agg_function"] == "dummy", "variable"])
    
    if len(dummies) > 0: 
        # Generate the dummies and add them to the data
        dat_dummies = pd.get_dummies(dat[dummies], prefix=dummies)
        dat = pd.concat([dat, dat_dummies], axis = 1)
        
        # Add new aggregation instructions for the dummies
        dummy_instructions = pd.DataFrame([[var, "max"] for var in dat_dummies.columns], columns=["variable", "agg_function"])
        aggregation_information = aggregation_information.append(dummy_instructions)
            
        # Remove old aggregation instructions
        aggregation_information = aggregation_information[~aggregation_information["variable"].isin(dummies)]
    
    # Aggregate all variables as requested
    data_aggregated = dat[aggregation_variable].drop_duplicates()
    
    aggregation_information = aggregation_information.reset_index(drop=True)

    for ind in tqdm(aggregation_information.index): 
        aggregated_col = aggregate_col(dat, aggregation_variable, 
                                       aggregation_information.loc[ind, "variable"], 
                                       aggregation_information.loc[ind, "agg_function"])

        data_aggregated = pd.merge(data_aggregated, aggregated_col, on = aggregation_variable)
        
    return data_aggregated

# Function to create data that integrates all above option, namely splitting, normalization, and aggregation
def create_data (data, split_info = None, normalization_info = None, normalization_variable = None, 
                 aggregation_category_dict = None, aggregation_category_variable = None, 
                 aggregation_information = None, aggregation_variable = None): 
    '''
    Function to create an aggregated dataset containing specified variables. 
    
    Parameters
    ----------
        
        data: pd df
            Raw data. Index will be disregarded should not be meaningful. 
        
        split_info: pd df with nested dict
            Instructions on the variables that need to be splitted. Some variables come as lists or
            strings. These need to be splitted into single variables. Example: 5,6. The split_info is a pd df
            with the two columns variable_name and values_and_labels. variable_name contains the names of the
            variables to be splitted. values_and_labels contains details on possible values and their labels.
            values_and_labels needs to be a dictionary. 
            Example: activities --> {'5': 'eating', '6': 'sleeping', '7': 'flying'}
        
        normalization_info: pd df
            File containing instructions for the normalization of a variable. 
            normalization_info is a pandas data frame with the first column containing the 
            rawstring and the following columns all applicable normalizations.
            Example 1: All tokens of prickly pear (e.g., prickly pear, pricklypear, opuntia) 
            should be normalized to "prickly pear".
            Example 2: "Vermillion and Ghila" is replaces with two entries named 
            "Vermillion fly catcher" and "Ghila woodpecker"
        
        normalization_variable: str
            The variable that needs to be normalized.
        
        aggregation_information: pd df
            Instructions for aggregation. This is a pd df with the two columns
            variable and agg_function. variable contains the variables that need to be aggregated. 
            agg_function specifies the function to be applied for aggreation. Currently implemented are
            mean, median, max, min, dummy, and one to six. One to six aggregate into 1 if the respective number
            is present and into 0 otherwise. Dummy creates dummy variables first and then aggregates using the 
            "max" function. NaNs are ignored.
            Note: This file needs to be in line with the split_info file. The newly created
            variables as defined in split info should be in aggregation_information, as needed. 
        
        aggregation_variable: str
            The variable along which we want to aggregate. This is the variable as it is named
            in data. This is likley to be the same as normalization_variable (e.g., bird species). 
        
        aggregation_category_dict: dict
            Used if aggregation on a categorical variable is desired. This usually
            relates to the variable that is normalized. For example, if we have animals and plants in our variable
            and we would like to combine all the animals into "animals" and all the plants into "plants" like
            "horse", "bird", "dog" -> animals and "bush", "tree", "cactus" -> plants. We would add a dict here
            that shows for every animal/plant if it is an animal or a plant. 
            
        aggregation_category_variable: str
            The variable to which the category aggregation is to be applied. 
        
    Returns
    -------
        pd df
        An aggregated dataset containing the variables specified in aggregation_information 
        and/or split_information. The variables are aggregated according to the instruction in the 
        aggregation_information file. 
    '''
    
    # Reset index of data (otherwise some function do not work properly)
    dat = data.reset_index(drop=True).copy()
    
    # Split the variables that need splitting
    if split_info is not None: 
        dat = split_multiple_categorical_vars(dat, split_info)
    
    # Get the dictionary for normalization
    if normalization_info is not None: 
        
        norm_dict = get_lookup(normalization_info)
        
        # Normalize org affiliation in data
        dat = normalize_data(dat, norm_dict, normalization_variable)
    
    # Replace string with aggregation string
    if aggregation_category_dict is not None:
        dat = repl_with_agg_string(dat, aggregation_category_variable, aggregation_category_dict)
    
    dat = dat.reset_index(drop=True)
    
    # Aggregate the data
    if aggregation_information is not None: 
        dat = aggregate_data(dat, aggregation_information, aggregation_variable)
        
    return dat


# HELPER FUNCTIONS
# Check for nan values in object that could be anything
# Source: https://stackoverflow.com/questions/944700/how-can-i-check-for-nan-values
def is_nan(x):
    return isinstance(x, float) and math.isnan(x)

# Check if object is just a single number
def response_length(x):
    
    if isinstance(x, int): 
        return 1
    else:
        return len(x)
    
# Function for the mean
def custom_mean(df):
    return df.mean(skipna=True)

# Function for the median
def custom_median(df):
    return df.median(skipna=True)

# Function for the max
def custom_max(df):
    return df.max(skipna=True)

# Function for the min
def custom_min(df):
    return df.min(skipna=True)

# Function for implementation
# Implementation is 1
def custom_one(df):
    '''This function is for aggregating pd df in combination with the groupby function. 
    It takes in a grouped df and returns 1 if any of the values is 1 and 0 otherwise.'''
    df_copy = df.copy()
    df_copy[df_copy != 1] = 0 
    df_copy[df_copy == 1] = 1 
    return df_copy.max(skipna=True)

# Function for implementation
# Implementation is 2
def custom_two(df):
    '''This function is for aggregating pd df in combination with the groupby function. 
    It takes in a grouped df and returns 1 if any of the values is 2 and 0 otherwise.'''
    df_copy = df.copy()
    df_copy[df_copy != 2] = 0 
    df_copy[df_copy == 2] = 1 
    return df_copy.max(skipna=True)

# Function for implementation
# Implementation is 3
def custom_three(df):
    '''This function is for aggregating pd df in combination with the groupby function. 
    It takes in a grouped df and returns 1 if any of the values is 3 and 0 otherwise.'''
    df_copy = df.copy()
    df_copy[df_copy != 3] = 0 
    df_copy[df_copy == 3] = 1 
    return df_copy.max(skipna=True)

# Function for implementation
# Implementation is 4
def custom_four(df):
    '''This function is for aggregating pd df in combination with the groupby function. 
    It takes in a grouped df and returns 1 if any of the values is 4 and 0 otherwise.'''
    df_copy = df.copy()
    df_copy[df_copy != 4] = 0 
    df_copy[df_copy == 4] = 1 
    return df_copy.max(skipna=True)

# Function for implementation
# Implementation is 5
def custom_five(df):
    '''This function is for aggregating pd df in combination with the groupby function. 
    It takes in a grouped df and returns 1 if any of the values is 5 and 0 otherwise.'''
    df_copy = df.copy()
    df_copy[df_copy != 5] = 0 
    df_copy[df_copy == 5] = 1 
    return df_copy.max(skipna=True)

# Function for implementation
# Implementation is 6
def custom_six(df):
    '''This function is for aggregating pd df in combination with the groupby function. 
    It takes in a grouped df and returns 1 if any of the values is 6 and 0 otherwise.'''
    df_copy = df.copy()
    df_copy[df_copy != 6] = 0 
    df_copy[df_copy == 6] = 1 
    return df_copy.max(skipna=True)