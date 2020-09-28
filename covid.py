import aiohttp

covid_url = 'https://api.covid19api.com/summary'


async def get_covid():
    async with aiohttp.ClientSession() as session:
        async with session.get(covid_url) as resp:
            # response = await resp.json()
            russia_info = (await resp.json())['Countries'][139]
    # russia_info = response['Countries'][139]
    covid_text = 'Коронавирус в России:\n\n' \
        'Новые случаи: {NewConfirmed}\n' \
        'Всего случаев: {TotalConfirmed}\n\n' \
        'Новых излечившихся: {NewRecovered}\n' \
        'Всего излечившихся: {TotalRecovered}\n\n' \
        'Новые погибшие: {NewDeaths}\n' \
        'Всего погибших: {TotalDeaths}' \
        .format(**russia_info)
    return covid_text
