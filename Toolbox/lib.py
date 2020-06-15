# -*- coding: UTF-8 -*-
# Copyright (C) 2018 Jean Bizot <jean@styckr.io>
""" Main lib for Toolbox Project
"""

from os.path import split
import pandas as pd
import datetime
import sys
import urllib.parse
import requests

pd.set_option('display.width', 200)


def clean_data(data):
    """ clean data
    """
    # Remove columns starts with vote
    cols = [x for x in data.columns if x.find('vote') >= 0]
    data.drop(cols, axis=1, inplace=True)
    # Remove special characteres from columns
    data.loc[:, 'civility'] = data['civility'].replace('\.', '', regex=True)
    # Calculate Age from day of birth
    actual_year = datetime.datetime.now().year
    data.loc[:, 'Year_Month'] = pd.to_datetime(data.birthdate)
    data.loc[:, 'Age'] = actual_year - data['Year_Month'].dt.year
    # Uppercase variable to avoid duplicates
    data.loc[:, 'city'] = data['city'].str.upper()
    # Take 2 first digits, 2700 -> 02700 so first two are region
    data.loc[:, 'postal_code'] = data.postal_code.str.zfill(5).str[0:2]
    # Remove columns with more than 50% of nans
    cnans = data.shape[0] / 2
    data = data.dropna(thresh=cnans, axis=1)
    # Remove rows with more than 50% of nans
    rnans = data.shape[1] / 2
    data = data.dropna(thresh=rnans, axis=0)
    # Discretize based on quantiles
    data.loc[:, 'duration'] = pd.qcut(data['surveyduration'], 10)
    # Discretize based on values
    data.loc[:, 'Age'] = pd.cut(data['Age'], 10)
    # Rename columns
    data.rename(columns={'q1': 'Frequency'}, inplace=True)
    # Transform type of columns
    data.loc[:, 'Frequency'] = data['Frequency'].astype(int)
    # Rename values in rows
    drows = {1: 'Manytimes', 2: 'Onetimebyday', 3: '5/6timesforweek',
             4: '4timesforweek', 5: '1/3timesforweek', 6: '1timeformonth',
             7: '1/trimestre', 8: 'Less', 9: 'Never'}
    data.loc[:, 'Frequency'] = data['Frequency'].map(drows)
    return data


BASE_URI = "https://www.metaweather.com"

def search_city(query):
    url = urllib.parse.urljoin(BASE_URI, "/api/location/search")
    cities = requests.get(url, params={'query': query}).json()
    if not cities:
        print(f"Sorry, Metaweather does not know about {query}...")
        return None
    if len(cities) == 1:
        return cities[0]
    for i, city in enumerate(cities):
        print(f"{i + 1}. {city['title']}")
        index = int(input("Oops, which one did you mean?")) - 1
        return cities[index]
    # TODO: Look for a given city and disambiguate between several candidates.
    #Return one city (or None)

def weather_forecast(woeid):
    # TODO: Return a 5-element list of weather forecast for a given woeid
    url = urllib.parse.urljoin(BASE_URI, f"/api/location/{woeid}")
    return requests.get(url).json()['consolidated_weather']

def query_weather():
    query = input("City?\n> ")
    city = search_city(query)
    # TODO: Display weather forecast for given city
    if city:
        daily_forecasts = weather_forecast(city['woeid'])
        for forecast in daily_forecasts:
            max_temp = round(forecast['max_temp'])
            print(f"{forecast['applicable_date']}: {forecast['weather_state_name']} ({max_temp}°C)")

def _check_arg_types(funcname, *args):
    hasstr = hasbytes = False
    for s in args:
        if isinstance(s, str):
            hasstr = True
        elif isinstance(s, bytes):
            hasbytes = True
        else:
            raise TypeError('%s() argument must be str or bytes, not %r' %
                            (funcname, s.__class__.__name__)) from None
    if hasstr and hasbytes:
        raise TypeError("Can't mix strings and bytes in path components") from None


if __name__ == '__main__':
    # For introspections purpose to quickly get this functions on ipython
    import Toolbox
    folder_source, _ = split(Toolbox.__file__)
    df = pd.read_csv('{}/data/data.csv.gz'.format(folder_source))
    clean_data = clean_data(df)
    print(' dataframe cleaned')
