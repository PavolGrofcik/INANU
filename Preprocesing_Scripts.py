#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 12:01:02 2018

@author: Pavol Grofčík
"""

import numpy as np
import pandas as pd
import re


###############################################################
#Here is a simle function that normalize it on format as follows
def format_date(date):
    if not isinstance(date, str):
        return date
    date=date.split(' ', 1)[0]
    x=re.findall(r"[\w']+", date)
    for i in x:
        year=0
        day=0
        if int(i)>31:
            year=x.index(i)
        elif int(i)>12:
            day=x.index(i)
            day = day
        if year==2:
            x[0], x[2] = x[2],x[0]
        date='-'.join(x)
    return date

###############################################################
    #Function returns dictionary keys
def dict_keys(dictionary):
    if (dictionary == None):
        return None
    
    keys = []
    
    for key in dictionary:
        keys.append(key)
        
    return keys

#Function returns dictionary values
def dict_values(dictionary):
    if(dictionary == None):
        return None
    
    values = []
    
    for key in dictionary:
        val = dictionary[key]
        values.append(val)
        
    return values

#Function returns dictionary from JSON format
def parse_json_col(med_info = None):
    
    if(med_info == None):
        return None
    
    med_info = med_info.strip("{}")  #Remove {}
    med_info = med_info.split(",")   #Separate into list by "," as a delimiter
    
    new = []
    
    for k in med_info:
        a,b = k.split(":")
        new.append(a.strip("'"))
        new.append(b.strip("'"))
        
    final = dict(new[i:i+2] for i in range(0,len(new),2))
    
    return final

#Final Function that creates new parsed columns
def add_columns(data = None, json_col = None):
    
    if (data[json_col].empty or json_col == None):
        return None
    
    #Creating empty columns from JSON row that we fill with values
    dictionary = parse_json_col(data[json_col][0])
    keys = dict_keys(dictionary)
    
    #New empty dataframe
    new = pd.DataFrame(columns=keys,index=range(len(data)))
    
    #Iteration over new dataframe and filling
    counter = 0
    for json in data[json_col]:
        try:
            if(np.isnan(json)):
                counter += 1
                new.loc[counter] = np.NaN
                continue
        except:
            pass

        json = parse_json_col(json)
        new.loc[counter] = dict_values(json)
        counter += 1

    
    cols = len(new.columns)
    
    for i in range(cols):
        col = new.pop(new.columns[0])
        name = keys[i]

        data[name] = col

    #New filled dataframe
    return data

################################################################
#Normalize Categorical columns
def normalize_identifiers(data, column):

    if(data[column].isna().any()):
        new_col = data[column].copy()
        
        for i in range(0,len(new_col)):
            if(pd.isna(new_col.iloc[i])):
                continue
            else:
                new_col.iloc[i] = new_col.iloc[i].lower()[0]
        data[column] = new_col.copy()
    else:
        data[column] = data[column].apply(lambda x : x.lower())
        data[column] = data[column].apply(lambda x :  x.replace(x,x[0]))
        data[data[column] == 'n'][column] = np.nan
        

def normalize_columns_booleans(data,df_new):
    
    """ The function normalize columns in dataframe 
        data, that contains values such as t.8,f.2...
        to the format t/f
        This function do nothing with Nan values
    """
    
    #iterating over the columns
    for col in df_new.columns:
  
        a = pd.unique(df_new[col])
        
        #List of valid values for normalization
        flags = ["f","t", "t.[0-9]", "f.[0-9]"]

        for item in a:

            #Normalization of values
            if(item in flags):
                normalize_identifiers(data=data,column=col)
                print("Normalized %s" % (col))
                break
            
################################################################
#Filling missing values
def fill_numeric_miss_values(data,column,method):
    
    """ The function fills missing numeric values
        with specific method. Method includes
        mean/med/mod.
    """
    methods = ["mean","med","mod"]
    
    if (data[column].isna().any() == False):
        #Stĺpec neobsahuje žiadne NaN hodnoty
        print("No missing values!")
        return
    
    #Creating a mask
    mask = data[column].isna()
    
    #Method check
    if(method not in methods):
        print("Invalid method")
        return
    
    #Determination of method
    if (method == "mean"):
        col = data[column]
        col = col[mask == False]
        value = np.mean(col)
        print(str.upper(method)," Value is:", value)
        
    elif (method == "med"):
        col = data[column]
        col = col[mask == False]
        value = col.mean()
        print(str.upper(method)," Value is:", value)

    elif (method == "mod"):
        col = data[column]
        col = col[mask == False]
        value = col.mode()[0]
        print(str.upper(method)," Value is:", value)

    #Replacing the missing value with the calculated one
    new_col = data[column].copy()
    for i in range(0,len(new_col)):

        if(pd.isna(new_col.iloc[i])):
            new_col.iloc[i] = value
   
    data[column] = new_col.copy()
    data[column] = data[column].astype("float64")
    
    print("Filling missing values by %s done!" % (str.upper(method)))
    
##################################################################
#Function that deletes outliers using boundary quartiles
#By deletion we mean converting to as Nan values
def normalize(data):
    #q1 = data.quantile(0.05) - 1.5 * stats.iqr(data)
    #q2 = data.quantile(0.95) + 1.5 * stats.iqr(data)
    
    q1 = data.quantile(0.05)
    q2 = data.quantile(0.95)
    
    mask_q1 = (data < q1)
    mask_q2 = (data > q2)
    
    data[mask_q1] = np.NaN
    data[mask_q2] = np.NaN
    
    #We return a new normalized column
    return data

#Function that normalize outliers with boundary quantiles 5% 95 %
def normalize_quantiles(column):
    column = column.apply(lambda x: float(x))
    
    if isinstance(column[0],str):
        print("Not numeric column!")
        return
    else:
        #We determine quantiles
        low = column.quantile(0.05)
        high = column.quantile(0.95)
        
        lmask = (column < low)
        hmask = (column > high)
        
        column[lmask] = column.median()
        column[hmask] = column.median()
        
        return column
    
#Function that transforms outliers by logaritm with base e
def log_transformation(column):
    low = column.quantile(0.05)
    high = column.quantile(0.95)
    med = column.quantile(0.5)
    
    lmask = (column < low)
    hmask = (column > high)
    
    low = np.power(low,np.log(med)/np.log(low))
    high = np.power(high,np.log(med)/np.log(high))
    
    #For values that outliers quantile we apply logarithmic transformation to median
    column[lmask] = low
    column[hmask] = high
    
    return column
#############################################################
    #Function that normalize categorical column in way of lower case
#and delimiting spaces
def format_categorical(column):
    length = len(column)
    
    for i in range(0,length):
        if (pd.isna(column[i])):
            continue
        else:
            val = column[i]
            val = val.lower()
            column[i] = " ".join(val.split())

    return column

############################################################
#Merging Datasets
#Here is a function that gets rid off duplicates and keeps data from other duplicates
def fill_from_duplicates(df, duplicates, indexes,df_new):
    """ This is function that get rid off duplicates in 
        dataframe df on indices indexes
    """
    
    indexes = indexes.tolist()
    
    #Iterating row by row
    for i in range(0, len(df)):
        if((i+1) == indexes[0]):
            
           #For Nan column we search over all duplicates to fill proper value
            for col in df.columns:
                if (pd.isnull(df.at[i,col]) or df.at[i,col] == "?"):
                    df.at[i,col] = df.at[i+1,col]
            
            indexes.pop(0)
            
            #Then we drop the duplicated row
            df.drop(i+1, inplace = True)
            if(len(indexes) == 0):
                #At the end we reset index
                df_new.reset_index(drop=True,inplace=True)
                print("Done")
                break
    
    