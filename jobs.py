from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import date

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
        'jornada': '',
        'zona': zone,
        'origen': '-1'
    }

    return requests.post(url, data=data)


def no_results(soup):
    return soup.find("p", {"class": "inforesultados"},
                     text="No se han encontrado resultados.")


def extract_jobs_from_request(soup):
    """Returns a list of job references (urls) from a soup

    Arguments:
        soup {[type]} -- [description]

    Returns:
        [list] -- List of urls (strings)
    """
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

    job["url"] = url

    return job


def process_jobs(jobs):
    """ Generates a Pandas dataframe with all the jobs found

    Arguments:
        jobs {list} -- List of jobs to be processed

    Returns:
        [Dataframe] -- Pandas dataframe with jobs
    """
    jobs_data = []
    for job in jobs:
        jobs_data.append(process_job(job))

    return pd.DataFrame(data=jobs_data)


def print_jobs(df):
    """ Prints a Pandas dataframe in HTML format

    Arguments:
        df {Pandas dataframe} -- Pandas dataframe with jobs information
    """
    # do not truncate text in dataframe option
    pd.set_option('display.max_colwidth', -1)

    html = df.to_html()
    filename = date.today().strftime("%Y-%m-%d") + ".html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write("<!doctype html>")
        file.write('<html lang="en">')
        file.write("<head>")
        file.write('<meta charset="utf-8">')
        file.write('<link rel="stylesheet" href="pure-min.css"')
        file.write("</head>")
        file.write("<body>")
        file.write('<section class="section">')
        file.write('<div class="container">')
        file.write(html)
        file.write('</div>')
        file.write('</section')
        file.write("</body>")
        file.write('</html>')


def search_jobs(zones):
    """ Search for jobs in the specified zones

    Arguments:
        zones {list} -- List of zones

    Returns:
        [Dataframe] -- Pandas dataframe with all jobs found
    """
    jobs = []
    for zone in zones:
        request = perform_search_request(zone[1])
        soup = BeautifulSoup(request.content, 'html.parser')
        jobs_zone = process_results(soup, zone[0])
        if jobs_zone:
            for job in jobs_zone:
                jobs.append(job)

    return process_jobs(jobs)

print_jobs((search_jobs(ZONES)))
