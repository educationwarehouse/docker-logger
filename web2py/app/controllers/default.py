import os

if False:
    from ..models.docker_logger_model import *

import bcrypt
import glob
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def index():
    """
    De indexpagina van de webapplicatie, hier kunnen we de gebruiker laten inloggen met het wachtwoord dat is opgeslagen in het .env-bestand.
    Dit omdat we alleen de logs willen laten zien aan geautoriseerde gebruikers die het wachtwoord hebben.
    """
    # Maak een formulier voor het inloggen met een wachtwoordveld (.env)
    form = SQLFORM.factory(Field("password", "password", label="Web2py token"))

    # Controleer of het formulier is ingediend
    if form.process().accepted:
        # Haal het wachtwoord uit het formulier
        password = form.vars.password

        # Haal de gehashte wachtwoord van de gebruiker uit de database
        user = db(db.auth_user.first_name == "token_user").select().first()
        hashed_password = user.password if user else None

        # Verifieer het wachtwoord
        if hashed_password and verify_password(password, hashed_password):
            # Log de gebruiker in en redirect naar de logs pagina
            auth.login_user(user)
            redirect(URL("logs"))
        else:
            response.flash = "Onjuist wachtwoord"

    # Render het formulier
    return dict(form=form)


def logs():
    # Fetch log filters from the database
    log_filters = db(db.log_filter).select()

    return dict(log_filters=log_filters)


def realtime_logs():
    """
    De logs pagina van de webapplicatie, hier kunnen we de logs van de Docker container laten zien.
    """
    # Get the filters from the URL
    url = urlparse(request.env.http_referer)
    filters = parse_qs(url.query).get("filters", [""])[0].split(",")
    search_terms = parse_qs(url.query).get("search", [""])[0].split(",")
    log_files = glob.glob("../logs/*.log", recursive=True)
    logs = []
    list_of_all_docker_names = []
    for log_file in log_files:
        # Extract the Docker name from the log file name
        docker_name = os.path.basename(log_file).split(".")[0]
        # Get all Docker names
        list_of_all_docker_names = [
            os.path.basename(log_file).split(".")[0]
            for log_file in glob.glob("../logs/*.log", recursive=True)
        ]

        with open(log_file, "r") as file:
            lines = file.readlines()
            if lines:
                for line in lines:
                    # Ignore lines containing `logs', because of the realtime logging with htmx
                    if "logs" in line and "debug" in line:
                        continue
                    # Only include the log if it matches one of the filters or search terms
                    if (not filters or any(filter in line for filter in filters)) and (
                        not search_terms
                        or any(search_term in line for search_term in search_terms)
                    ):
                        # Extract the datetime string from the log line
                        datetime_str = line[
                            :26
                        ]  # Adjust this to include the milliseconds
                        # Convert the datetime string to a datetime object
                        timestamp = datetime.strptime(
                            datetime_str, "%Y-%m-%dT%H:%M:%S.%f"
                        )
                        logs.append((docker_name, timestamp, line))

    # Sort the logs by datetime
    logs = sorted(logs, key=lambda log: log[1])
    logs = logs[-10:]
    if list_of_all_docker_names == []:
        list_of_all_docker_names = ["No logs available"]
    return dict(logs=logs, docker_names=list_of_all_docker_names)


def get_docker_names():
    docker_names = [os.path.basename(log_file).split('.')[0] for log_file in glob.glob('../logs/*.log', recursive=True)]
    return response.json(docker_names)

def add_items():
    term = request.vars.term
    url = request.vars.url
    name = request.vars.name
    if term:
        print("Inserting search term:", term, "with the name:", name if name else term)
        db.search_term.insert(term=[term, name])
    if url:
        print("Inserting url:", url, "with the name:", name if name else url)
        db.url.insert(url=[url, name])
    db.commit()
    redirect(URL("logs"))


def get_search_terms():
    search_terms = db(db.search_term).select()
    return response.json([term.term for term in search_terms])


def get_urls():
    urls = db(db.url).select()
    return response.json([url.url for url in urls])


def delete_item():
    term = request.vars.term
    url = request.vars.url
    name = request.vars.name
    if term:
        print("Deleting search term:", term, "with the name:", name if name else term)
        db(db.search_term.term.contains(term)).delete()
    if url:
        print("Deleting url:", url, "with the name:", name if name else url)
        db(db.url.url.contains(url)).delete()
    db.commit()
    redirect(URL("logs"))