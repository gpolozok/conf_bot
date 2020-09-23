import requests

covid_url = 'https://api.covid19api.com/summary'

def get_covid():
    response = requests.get(covid_url)
    russia_info = response.json()['Countries'][139]
    covid_text = 'Коронавирус в России:\n\n' \
        'Новые случаи: {NewConfirmed}\n' \
        'Всего случаев: {TotalConfirmed}\n\n' \
        'Новых излечившихся: {NewRecovered}\n' \
        'Всего излечившихся: {TotalRecovered}\n\n' \
        'Новые погибшие: {NewDeaths}\n' \
        'Всего погибших: {TotalDeaths}' \
        .format(**russia_info)   
    return covid_text