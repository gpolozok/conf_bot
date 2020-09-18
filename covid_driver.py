import requests

covid_url = 'https://api.covid19api.com/summary'

def get_covid():
    response = requests.get(covid_url)
    info = response.json()['Countries']
    return (info[139]['NewConfirmed'], info[139]['TotalConfirmed'],
            info[139]['NewRecovered'], info[139]['TotalRecovered'],
            info[139]['NewDeaths'], info[139]['TotalDeaths'])