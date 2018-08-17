from bs4 import BeautifulSoup
import requests
import numpy
import pandas
import os
import folium

def clear_csv_file(filename):
    """
    Removes csv file
    """
    if(os.path.exists(filename)):
        os.remove(filename)

def get_wingstop_state_locations(location_url):
    """
    Get participating wingstop state locations in the US
    """
    locations_page = requests.get(location_url)
    soup_object = BeautifulSoup(locations_page.text, 'html.parser')
    participating_states = soup_object.find(id="ParticipatingStates").find_all('a')
    return [participating_state['href'].split('/')[2] for participating_state in participating_states]

def get_location_list(location_url, state_name):
    """
    Get wingstop address information for a given state
    """
    page = requests.get(location_url + '/' + state_name)
    soup = BeautifulSoup(page.text, 'html.parser')
    locations = soup.find(id="ParticipatingRestaurants").find_all(class_="streetaddress adr")
    state_information = dict()
    for index, location in enumerate(locations):
        state_information[index] = dict()
        location_address = location.find_all('span')
        state_information[index]['address'] = location_address[0].contents[0].strip()
        state_information[index]['city'] = location_address[1].contents[0].strip()
        state_information[index]['state'] = location_address[2].contents[0].strip()
    return pandas.DataFrame(state_information).transpose()


def get_latitude_longitude(address, city, state):
    mapping_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
    split_address = '+'.join(address.split(" "))
    split_city = '+'.join(city.split(" "))
    split_state = '+'.join(state.split(" "))
    string = mapping_url + split_address + ",+" + split_city + ",+" + split_state
    response = requests.get(string).json()
    try:
        location = response['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    except:
        return None, None


def create_list_of_locations(state_informations):
    """
    Writes to a specified csv file
    """
    df = pandas.DataFrame(columns=['latitude', 'longitude'])
    for key in state_informations.index:
        lat, lng = get_latitude_longitude(
            state_informations.iloc[key]['address'], state_informations.iloc[key]['city'], state_informations.iloc[key]['state'])
        if lat == None and lng == None:
            pass
        else: 
            df.loc[key] = [lat, lng]
    return df

def main():
    """
    Scrapes wingstop location for the amount of wingstop in the state
    """
    filename = "test_data.txt"
    location_url = 'https://order.wingstop.com/locations'
    clear_csv_file(filename)
    df = pandas.DataFrame()
    print('Getting wingstop state information')
    state_names = get_wingstop_state_locations(location_url)
    for state_name in state_names:
        state_information = get_location_list(location_url, state_name)
        df = pandas.concat([df, create_list_of_locations(state_information)])
    print('Finish with get coordinates')
    df.to_csv('coordinates.csv', index=False)

if __name__ == "__main__":
    main()
