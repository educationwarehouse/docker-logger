import os

if False:
    from ..models.docker_logger_model import *

import bcrypt
import glob



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


from pathlib import Path

def logs():
    """
    De logs pagina van de webapplicatie, hier kunnen we de logs van de Docker container laten zien.
    """
    # Vind alle .log bestanden in de parent directory van de huidige map en alle submappen
    log_files = glob.glob('../logs/*.log', recursive=True)
    logs = []
    for log_file in log_files:
        with open(log_file, 'r') as file:
            lines = file.readlines()
            for line in lines:
                print(line)
                logs.append(line)

    return dict(logs=logs)
















