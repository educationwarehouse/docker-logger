import os

if False:
    from ..models.docker_logger_model import *

import bcrypt
import glob
import os
from datetime import datetime



def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

def index():
    """
    De indexpagina van de webapplicatie, hier kunnen we de gebruiker laten inloggen met het wachtwoord dat is opgeslagen in het .env-bestand.
    Dit omdat we alleen de logs willen laten zien aan geautoriseerde gebruikers die het wachtwoord hebben.
    """
    # Maak een formulier voor het inloggen met een wachtwoordveld (.env)
    form = SQLFORM.factory(Field('password', 'password', label='Web2py token'))

    # Controleer of het formulier is ingediend
    if form.process().accepted:
        # Haal het wachtwoord uit het formulier
        password = form.vars.password

        # Haal de gehashte wachtwoord van de gebruiker uit de database
        user = db(db.auth_user.first_name == 'token_user').select().first()
        hashed_password = user.password if user else None

        # Verifieer het wachtwoord
        if hashed_password and verify_password(password, hashed_password):
            # Log de gebruiker in en redirect naar de logs pagina
            auth.login_user(user)
            redirect(URL('logs'))
        else:
            response.flash = 'Onjuist wachtwoord'

    # Render het formulier
    return dict(form=form)


def logs():
    """
    De logs pagina van de webapplicatie, hier kunnen we de logs van de Docker container laten zien.
    """
    log_files = glob.glob('../logs/*.log', recursive=True)
    logs = []
    for log_file in log_files:
        # Extract the Docker name from the log file name
        docker_name = os.path.basename(log_file).split('.')[0]
        with open(log_file, 'r') as file:
            lines = file.readlines()
            if lines:
                for line in lines:
                    # Ignore lines containing `logs', because of the realtime logging with htmx
                    if 'logs' in line:
                        continue
                    # Extract the datetime string from the log line
                    datetime_str = line[:26]  # Adjust this to include the milliseconds
                    # Convert the datetime string to a datetime object
                    timestamp = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")
                    logs.append((docker_name, timestamp, line))

    # Sort the logs by datetime
    logs = sorted(logs, key=lambda log: log[1])

    return dict(logs=logs)


