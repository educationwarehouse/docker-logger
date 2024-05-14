import os

if False:
    from ..models.docker_logger_model import *

import bcrypt
import glob
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import re


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

    return dict(
        log_filters=log_filters,
        docker_names=get_docker_names(),
        search_terms=get_search_terms(),
        urls=get_urls(),
        request_current_url=request.env.http_referer,
    )


def get_docker_names():
    log_files = glob.glob("../logs/*.log", recursive=True)
    docker_names = []
    for log_file in log_files:
        docker_name = os.path.basename(log_file).split(".")[0]
        docker_names.append(docker_name)
    return docker_names


def get_search_terms():
    search_terms = db(db.search_term).select(db.search_term.term)
    return search_terms


def get_urls():
    urls = db(db.url).select(db.url.url)
    return urls


def realtime_logs():
    """
    De logs pagina van de webapplicatie, hier kunnen we de logs van de Docker container laten zien.
    """
    # Get the filters from the URL
    url = urlparse(request.env.http_referer)
    filters = parse_qs(url.query).get("filters", [""])[0].split(",")
    search_terms = parse_qs(url.query).get("search", [""])[0].split(",")
    exclude_docker_names = parse_qs(url.query).get("exclude", [""])[0].split(",")
    collapse_timestamp = parse_qs(url.query).get("timestamp", [""])[0]
    log_files = glob.glob("../logs/*.log", recursive=True)
    logs = []
    for log_file in log_files:
        # Extract the Docker name from the log file name
        docker_name = os.path.basename(log_file).split(".")[0]
        # Skip this log file if its docker name is in the list of docker names to exclude
        if docker_name in exclude_docker_names:
            continue

        with open(log_file, "r") as file:
            lines = file.readlines()
            if lines:
                for line in lines:
                    # Ignore lines containing `logs', because of the realtime logging with htmx
                    if "logs" in line and "debug" in line:
                        continue
                    # Only include the log if it matches one of the filters or search terms
                    if (
                        not filters
                        or any(filter.lower() in line.lower() for filter in filters)
                    ) and (
                        not search_terms
                        or any(
                            re.search(search_term.lower(), line.lower())
                            for search_term in search_terms
                        )
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
    logs = sorted(logs, key=lambda log: log[1], reverse=True)
    logs = logs[:100]
    return dict(logs=logs, collapse_timestamp=collapse_timestamp)


def manipulate_url(url, param_name, param_value):
    # Parse the URL into components
    url_parts = urlparse(url)
    # Parse the URL parameters
    params = parse_qs(url_parts.query)

    if param_value:
        # If the parameter already exists, append the new value
        if param_name in params:
            # Avoid duplicate search terms
            if param_value not in params[param_name][0].split(","):
                params[param_name][0] += "," + param_value
        else:
            # Otherwise, set the parameter
            params[param_name] = [param_value]
    elif param_name in params:
        # Remove the parameter
        del params[param_name]

    # Construct the updated URL
    updated_url = url_parts._replace(query=urlencode(params, doseq=True)).geturl()
    # Replace '%2C' with a comma
    updated_url = updated_url.replace("%2C", ",")
    updated_url = updated_url.split("default/")[1]
    return updated_url


def add_filters_to_url():
    filters = request.vars["filter"]
    new_url = manipulate_url(request.env.http_referer, "filters", filters)
    redirect(URL(new_url))


def add_searches_to_url():
    search_terms = request.vars["search"]
    new_url = manipulate_url(request.env.http_referer, "search", search_terms)
    redirect(URL(new_url))


def add_docker_names_to_url():
    docker_names = request.vars["docker_name"]
    new_url = manipulate_url(request.env.http_referer, "exclude", docker_names)
    redirect(URL(new_url))


def add_to_search_bar(item, search_input):
    if search_input:
        search_input += ","
    search_input += item
    return search_input


def clear_url():
    redirect(URL("default", "logs"))


def collapse_date_column():
    # Get the current URL from the request environment
    url = request.env.http_referer

    # Parse the URL into components
    url_parts = urlparse(url)
    # Parse the URL parameters
    params = parse_qs(url_parts.query)

    if "timestamp" in params:
        # If the Datum column was not visible, remove 'timestamp' from the URL
        updated_url = manipulate_url(url, "timestamp", "")
    else:
        # If the Datum column was visible, add 'timestamp=false' to the URL
        updated_url = manipulate_url(url, "timestamp", "false")

    redirect(URL(updated_url))


def submit_item():
    term = request.vars["default-term"]
    url = request.vars["default-url"]
    name = request.vars["nickname"]
    if term:
        print("Inserting search term:", term, "with the name:", name if name else term)
        db.search_term.insert(term=[term, name])
    if url:
        print("Inserting url:", url, "with the name:", name if name else url)
        db.url.insert(url=[url, name])
    db.commit()
    redirect(URL("logs"))


def delete_item():
    item_type = request.vars.item_type
    item = request.vars.item
    name = request.vars.name
    if item_type == "term":
        db(db.search_term.term.contains(item)).delete()
    elif item_type == "url":
        db(db.url.url.contains(item)).delete()
    db.commit()
    redirect(URL("logs"))


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
