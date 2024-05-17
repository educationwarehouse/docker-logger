if False:
    from ..models.docker_logger_model import *

import bcrypt
import glob
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import re


def verify_password(password, hashed_password):
    """
    Checks if a password matches a hashed password.

    Parameters:
    password (str): The plain text password provided by the user.
    hashed_password (str): The hashed password stored in the database.

    Returns:
    bool: True if the password matches the hashed password, False otherwise.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def index():
    """
    It allows the user to log in only using a password stored in the .env file.
    Because only authorized users who have the password can view the logs.

    Returns:
    dict: A dictionary containing the form for rendering in the view.
    """
    # only needs to use a password to login because otherwise someone needs to create an account
    # and web2py also only needs a password to see the admin interface
    form = SQLFORM.factory(Field("password", "password", label="Web2py token"))

    if form.process().accepted:
        password = form.vars.password

        user = db(db.auth_user.first_name == "token_user").select().first()
        hashed_password = user.password if user else None

        if hashed_password and verify_password(password, hashed_password):
            auth.login_user(user)
            redirect(URL("logs"))
        else:
            response.flash = "Incorrect password"

    return dict(form=form)


def get_docker_names():
    """
    This function retrieves the names of all Docker containers for which log files exist in the '../logs/' directory.

    Returns:
    list: A list of Docker container names.
    """
    all_docker_log_files = glob.glob("../logs/*.log", recursive=True)
    docker_names = []
    for log_file in all_docker_log_files:
        # Extract the Docker container name from the log file name (without the '.log' extension)
        docker_name = os.path.basename(log_file).split(".")[0]
        docker_names.append(docker_name)
    return docker_names


def generate_docker_colors(docker_names):
    """
    Generates a color for each Docker container.

    Parameters:
    docker_names (list): A list of Docker container names.

    Returns:
    dict: A dictionary where the keys are Docker container names and the values are the corresponding colors.
    """
    return {docker_name: string_to_color(docker_name) for docker_name in docker_names}


def get_db_items(table_name, field_names):
    """
    Retrieves items from a specified table in the database.

    Parameters:
    table_name (str): The name of the table.
    field_names (list): A list of the names of the fields to retrieve.

    Returns:
    Rows: A Rows object containing the retrieved items.
    """
    return db(db[table_name]).select(*[db[table_name][field] for field in field_names])


def get_url_items(request_vars_name):
    """
    Splits a comma-separated string into a list of items.

    Parameters:
    request_vars_name (str): A comma-separated string.

    Returns:
    list: A list of items. If `request_vars_name` is `None` or an empty string, returns an empty list.
    """
    return request_vars_name.split(",") if request_vars_name else []


@auth.requires_login()
def logs():
    """
    This function retrieves the necessary data to render the logs page of the web application;
        It retrieves the names of all Docker containers for which log files exist,
        the Docker container names that are excluded from the logs,
        generates a dictionary where the keys are Docker container names and the values are the corresponding colors,
        retrieves the log filters from the database,
        the log filters that are applied to the logs,
        retrieves the search terms from the database,
        the search terms that are applied to the logs,
        and retrieves the URLs from the database.

    Returns:
    dict: A dictionary containing the Docker container names, the excluded Docker container names,
    the Docker container colors, the log filters, the applied log filters, the search terms,
    the applied search terms, and the URLs.
    """
    docker_names = get_docker_names()
    url_docker_names = get_url_items(request.vars.exclude)
    docker_colors = generate_docker_colors(docker_names)
    filters = get_db_items("log_filter", ["log_filter"])
    url_filters = get_url_items(request.vars.filters)
    search_terms = get_db_items("search_term", ["term", "name"])
    url_search_terms = get_url_items(request.vars.search)
    urls = get_db_items("url", ["url", "name"])
    return dict(
        url_docker_names=url_docker_names,
        docker_names=docker_names,
        docker_colors=docker_colors,
        filters=filters,
        url_filters=url_filters,
        search_terms=search_terms,
        url_search_terms=url_search_terms,
        urls=urls,
    )


def parse_url(term):
    """
    Parses the URL parameters from the HTTP request.

    Parameters:
    term (str): The name of the URL parameter.

    Returns:
    str or list: If `term` is "timestamp", returns the value of the "timestamp" parameter from the URL query string or
    an empty string if the "timestamp" parameter does not exist.
    If `term` is not "timestamp", returns a list of values of the specified parameter from the URL query string or
    an empty list if the specified parameter does not exist.
    """
    url = urlparse(request.env.http_referer)
    if term == "timestamp":
        return parse_qs(url.query).get(term, [""])[0]
    return parse_qs(url.query).get(term, [""])[0].split(",")


@auth.requires_login()
def realtime_logs():
    """
    Retrieves the logs of the Docker containers, sorts them by datetime.

    Returns:
    dict: A dictionary containing the logs, a flag indicating whether the timestamp is collapsed,
    and the Docker container colors.
    """
    logs = process_log_files()
    # Sort the logs by datetime, in descending order
    # so that the most recent logs are displayed first
    logs = sorted(logs, key=lambda log: log[1], reverse=True)
    logs = logs[:100]

    docker_names = get_docker_names()

    docker_colors = {
        docker_name: string_to_color(docker_name) for docker_name in docker_names
    }

    return dict(
        logs=logs,
        collapse_timestamp=parse_url("timestamp"),
        docker_colors=docker_colors,
    )


def process_log_files():
    """
    Processes the (real time) log files of Docker containers.

    Returns:
    list: A list of tuples. Each tuple contains a Docker container name, a timestamp, and a log line.
    """
    logs = []
    docker_names = get_docker_names()
    for docker_name in docker_names:
        if docker_name in parse_url("exclude"):
            continue
        log_file = f"../logs/{docker_name}.log"
        with open(log_file, "r") as file:
            lines = file.readlines()
            if lines:
                for line in lines:
                    # Skip the line if it contains the string "logs" and "debug" and 'X-Forwarded-Host\\":[\\"logs.'
                    # This is a known line, but it is not relevant for the logs, because the logs will refresh every
                    # second and this line will be displayed every time.
                    if (
                        "logs" in line
                        and "debug" in line
                        and 'X-Forwarded-Host\\":[\\"logs.' in line
                    ):
                        continue
                    if (
                        not parse_url("filters")
                        or any(
                            filter.lower() in line.lower()
                            for filter in parse_url("filters")
                        )
                    ) and (
                        not parse_url("search")
                        or any(
                            re.search(search_term, line.lower(), flags=re.IGNORECASE)
                            for search_term in parse_url("search")
                        )
                    ):
                        datetime_str = line[:26]
                        timestamp = datetime.strptime(
                            datetime_str, "%Y-%m-%dT%H:%M:%S.%f"
                        )
                        logs.append((docker_name, timestamp, line))
    return logs


def manipulate_url(url, param_name, param_values):
    """
    Manipulates the URL parameters by adding, updating, or removing a specified URL parameter.

    Parameters:
    url (str): The URL to be manipulated.
    param_name (str): The name of the URL parameter to be manipulated.
    param_values (str or list): The new values for the URL parameter. If `param_values` is `None`,
    the URL parameter is removed.

    Returns:
    str: The updated URL.
    """
    url_parts = urlparse(url)
    params = parse_qs(url_parts.query)

    # make it a list if it is a string, because we want to iterate over it
    if isinstance(param_values, str):
        param_values = [param_values]

    # removing the parameter if it is not in the URL
    if param_values is None:
        if param_name in params:
            del params[param_name]
    else:
        # updating the parameter if it is in the URL
        if param_name in params:
            existing_values = params[param_name][0].split(",")
            updated_values = []
            for value in existing_values:
                if value in param_values:
                    updated_values.append(value)
            for value in param_values:
                if value not in existing_values:
                    updated_values.append(value)
            params[param_name] = [",".join(updated_values)]
        # adding the parameter if it is not in the URL
        else:
            if param_values:
                params[param_name] = [",".join(param_values)]

    updated_url = url_parts._replace(query=urlencode(params, doseq=True)).geturl()
    # replace %2C with a comma, because it is more readable and the user can understand it and manipulate it easier
    updated_url = updated_url.replace("%2C", ",")
    updated_url = updated_url.split("default/")[1]
    return updated_url


def add_value_to_url():
    """
    Adds or updates a parameter in the URL using the manipulate_url function.
    """
    param_name = request.vars["param_name"]
    param_values = request.vars["param_values"]
    new_url = manipulate_url(request.env.http_referer, param_name, param_values)
    redirect(URL(new_url))


def clear_url():
    """
    Redirects the user to the logs page of the web application.

    This function does not take any parameters. It simply redirects the user to the logs page, effectively clearing any
    URL parameters that may have been set.
    """
    redirect(URL("default", "logs"))


def collapse_date_column():
    """
    Toggles the visibility of the timestamp column in the logs using the manipulate_url function.
    """
    url = request.env.http_referer

    url_parts = urlparse(url)
    params = parse_qs(url_parts.query)

    if "timestamp" in params:
        updated_url = manipulate_url(url, "timestamp", None)
    else:
        updated_url = manipulate_url(url, "timestamp", "false")

    redirect(URL(updated_url))


def submit_or_delete_item():
    """
    Submits or deletes an item based on the value of `submit_or_delete`.

    The function first retrieves the term, URL, nickname, and the action (either "submit" or "delete")
    from the HTTP request variables.
    If the action is "submit", it calls the `model_submit_item` function to submit the item.
    If the action is "delete", it calls the `model_delete_item` function to delete the item.
    """
    term = request.vars["default-term"]
    url = request.vars["default-url"]
    name = request.vars["nickname"]
    submit_or_delete = request.vars["submit_or_delete"]
    if submit_or_delete == "submit":
        model_submit_item(term, url, name)
    else:
        model_delete_item(term, url, name)
    redirect(URL("logs"))


def string_to_color(input_string):
    """
    Converts a given string into a color code in hexadecimal format.

    This function first calculates a hash code of the input string. It then extracts the red (r), green (g),
    and blue (b) components from the hash code. The result is then increased by 100 to ensure the color is not too dark.
    The values of r, g, and b are then limited to a maximum of 255. Finally, it returns a string in the format of a
    hexadecimal color code, such as #RRGGBB, where RR, GG, and BB are two-digit hexadecimal values of the red,
    green, and blue components.
    This way we can generate a unique color for each input string, and hold the color consistent for the same input string.

    Parameters:
    input_string (str): The input string to be converted into a color code.

    Returns:
    str: The color code in hexadecimal format.
    """
    hash_code = hash(input_string)
    r = ((hash_code & 0xFF0000) >> 16) + 100
    g = ((hash_code & 0x00FF00) >> 8) + 100
    b = (hash_code & 0x0000FF) + 100
    r = min(255, r)
    g = min(255, g)
    b = min(255, b)
    return "#{:02x}{:02x}{:02x}".format(r, g, b)
