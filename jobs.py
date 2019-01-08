from bs4 import BeautifulSoup
import requests
import pandas as pd

BASE_URL = 'http://www.cofm.es/es'
SEARCH = '/tratarAplicacionOfertasEmpleo.do'
ZONES = [
    ('Alcorcon', '13'),
    ('Getafe', '77'),
    ('Fuenlabrada', '67'),
    ('Leganes', '89'),
    ('Mostoles', '181'),
    ('Humanes', '88')
]
JOB_FIELDS = [
    'Referencia',
    'Actividad',
    'Tipo de Trabajo',
    'Descripción',
    'Zona',
    'Jornada',
]
JOB_CONTACT = [
    'Persona de Contacto',
    'Teléfono',
    'E-mail'
]


def perform_search_request(zone):
    '''Perform a search request to get the jobs in COFM for
    the zone specified as parameter.
    Arguments:
        zone {string} -- Job search zone
    Returns:
        request -- Job request for the specified zone
    '''

    url = BASE_URL + SEARCH
    data = {
        'actividad': '0',
        'experiencia': '-1',
        'tipo': '1',
        'jornada': 'M',
        'zona': zone,
        'origen': '-1'
    }

    return requests.post(url, data=data)


def no_results(soup):
    return soup.find("p", {"class": "inforesultados"},
                     text="No se han encontrado resultados.")


def extract_jobs_from_request(soup):
    jobs_section = soup.find("div", {"class": "listado_tabla"})
    jobs_references = [BASE_URL + td.find('a')['href'] for td in
                       jobs_section.findChildren("td", {"class": "td-icono"})]
    return jobs_references


def process_results(soup, zone):
    if no_results(soup):
        # print('No results for zone ', zone)
        pass
    else:
        jobs = extract_jobs_from_request(soup)
        # print("{} Jobs in {}".format(len(jobs), zone))
        return jobs


def get_job_and_contact_info(url):
    request = requests.get(url)
    soup = BeautifulSoup(request.content, 'html.parser')
    info = soup.find_all("ul", {"class": "datos-ficha"})

    return info[0].find_all("li"), info[1].find_all("li")


def process_job(url):
    job_info, contact_info = get_job_and_contact_info(url)
    job = {}

    for idx, field in enumerate(JOB_FIELDS):
        job[field] = job_info[idx].find("span").text.\
                                   strip().replace('\t', '   ').\
                                   replace('\n', ' ').\
                                   replace('\r', ' ')

    for idx, field in enumerate(JOB_CONTACT):
        job[field] = contact_info[idx].find("span").text.\
                                       strip().replace('\t', '   ').\
                                       replace('\n', ' ').\
                                       replace('\r', ' ')

    return job


def process_jobs(jobs):
    # do not truncate text in dataframe option
    pd.set_option('display.max_colwidth', -1)

    jobs_data = []
    for job in jobs:
        jobs_data.append(process_job(job))

    df = pd.DataFrame(data=jobs_data)
    print(df.to_html())


def search_jobs():
    jobs = []
    for zone in ZONES:
        request = perform_search_request(zone[1])
        soup = BeautifulSoup(request.content, 'html.parser')
        jobs_zone = process_results(soup, zone[0])
        if jobs_zone:
            for job in jobs_zone:
                jobs.append(job)
    process_jobs(jobs)

search_jobs()
