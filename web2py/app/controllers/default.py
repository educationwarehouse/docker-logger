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
    # get all the filters from the database
    filters = db(db.log_filter).select(db.log_filter.log_filter)

    # Get the filters from the request variables
    url_filters = request.vars.filters.split(",") if request.vars.filters else []

    # get the Docker names from the log files
    log_files = glob.glob("../logs/*.log", recursive=True)
    docker_names = []
    for log_file in log_files:
        docker_name = os.path.basename(log_file).split(".")[0]
        docker_names.append(docker_name)

    # get the docker names from the request variables
    url_docker_names = request.vars.exclude.split(",") if request.vars.exclude else []

    # get all the search terms from the database
    search_terms = db(db.search_term).select(db.search_term.term, db.search_term.name)

    # get the search terms from the request variables
    url_search_terms = request.vars.search.split(",") if request.vars.search else []

    # get the urls from the database
    urls = db(db.url).select(db.url.url, db.url.name)

    # generate a color for each docker name
    docker_colors = {
        docker_name: string_to_color(docker_name) for docker_name in docker_names
    }

    return dict(
        filters=filters,
        url_filters=url_filters,
        url_docker_names=url_docker_names,
        docker_names=docker_names,
        search_terms=search_terms,
        url_search_terms=url_search_terms,
        urls=urls,
        docker_colors=docker_colors,
    )


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
                    if (
                        "logs" in line
                        and "debug" in line
                        and 'X-Forwarded-Host\\":[\\"logs.' in line
                    ):
                        continue
                    # Only include the log if it matches one of the filters or search terms
                    if (
                        not filters
                        or any(filter.lower() in line.lower() for filter in filters)
                    ) and (
                        not search_terms
                        or any(
                            re.search(search_term, line.lower(), flags=re.IGNORECASE)
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

    log_files = glob.glob("../logs/*.log", recursive=True)
    docker_names = []
    for log_file in log_files:
        docker_name = os.path.basename(log_file).split(".")[0]
        docker_names.append(docker_name)
    docker_colors = {
        docker_name: string_to_color(docker_name) for docker_name in docker_names
    }

    return dict(
        logs=logs, collapse_timestamp=collapse_timestamp, docker_colors=docker_colors
    )


def manipulate_url(url, param_name, param_values):
    # Parse the URL into components
    url_parts = urlparse(url)
    # Parse the URL parameters
    params = parse_qs(url_parts.query)

    # If param_values is a string, convert it to a list
    if isinstance(param_values, str):
        param_values = [param_values]

    if param_values is None:
        # If param_values is None, remove the parameter
        if param_name in params:
            del params[param_name]
    else:
        # If the parameter already exists, check the values
        if param_name in params:
            # Split the existing values
            existing_values = params[param_name][0].split(",")
            # Create a list to store the updated values
            updated_values = []
            # Iterate over the existing values
            for value in existing_values:
                # If the value is in the provided list, add it to the updated values
                if value in param_values:
                    updated_values.append(value)
            # Iterate over the provided list
            for value in param_values:
                # If the value is not in the existing values, add it to the updated values
                if value not in existing_values:
                    updated_values.append(value)
            # Set the parameter to the updated values
            params[param_name] = [",".join(updated_values)]
        else:
            # If the parameter does not exist and param_values is not empty, set the parameter
            if param_values:
                params[param_name] = [",".join(param_values)]

    # Construct the updated URL
    updated_url = url_parts._replace(query=urlencode(params, doseq=True)).geturl()
    # Replace '%2C' with a comma
    updated_url = updated_url.replace("%2C", ",")
    updated_url = updated_url.split("default/")[1]
    return updated_url


def add_filters_to_url():
    print(request.vars)
    filters = request.vars["filter"]
    new_url = manipulate_url(request.env.http_referer, "filters", filters)
    redirect(URL(new_url))


def add_searches_to_url():
    search_terms = request.vars["search"]
    new_url = manipulate_url(request.env.http_referer, "search", search_terms)
    redirect(URL(new_url))


def add_docker_names_to_url():
    print(request.vars)
    docker_names = request.vars["docker_name"]
    new_url = manipulate_url(request.env.http_referer, "exclude", docker_names)
    redirect(URL(new_url))


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
        updated_url = manipulate_url(url, "timestamp", None)
    else:
        # If the Datum column was visible, add 'timestamp=false' to the URL
        updated_url = manipulate_url(url, "timestamp", "false")

    redirect(URL(updated_url))


def submit_item():
    term = request.vars["default-term"]
    url = request.vars["default-url"]
    name = request.vars["nickname"]
    model_submit_item(term, url, name)
    redirect(URL("logs"))


def delete_item():
    term = request.vars["default-term"]
    url = request.vars["default-url"]
    name = request.vars["nickname"]
    model_delete_item(term, url, name)
    redirect(URL("logs"))


def string_to_color(input_string):
    hash_code = hash(input_string)
    r = ((hash_code & 0xFF0000) >> 16) + 100
    g = ((hash_code & 0x00FF00) >> 8) + 100
    b = (hash_code & 0x0000FF) + 100
    r = min(255, r)
    g = min(255, g)
    b = min(255, b)
    return "#{:02x}{:02x}{:02x}".format(r, g, b)
