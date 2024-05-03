import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import edwh
    import edwh.tasks  # stupide pycharm!
    import tomlkit
    from invoke import Context, Result, run, task
    from termcolor import colored
except ImportError as e:
    if sys.argv[0].split("/")[-1] in {"inv", "invoke"}:
        print(
            "WARNING: this tasks.py works best using the edwh command instead of using inv[oke] directly."
        )
        print("Example:")
        if sys.argv[1].startswith("-"):
            print("> edwh", " ".join(sys.argv[1:]))
        else:
            print("> edwh local." + " ".join(sys.argv[1:]))
        print()

    print(
        "Install edwh using `pipx install edwh[omgeving]` to automatically install edwh and all dependencies."
    )
    print(
        "Or install using `pip install -r requirements.txt` in an appropriate virtualenv when not using edwh. "
    )
    print()
    print("ImportError:", e)

    exit(1)

current_folder = Path(".").absolute().name

config = dict(
    services=dict(services="discover", minimal=[], include_celeries_in_minimal=False),
)

toml_file = Path("config.toml")
if toml_file.exists():
    config.clear()
    config |= tomlkit.parse(toml_file.read_text())
else:
    print(
        "ERROR: config.toml not found. Run `edwh setup` to create a new config file.",
        file=sys.stderr,
    )

@task()
def setup(c):
    """Setup or update the ontwikkel_omgeving environment."""
    c: Context

    print("Setting up/updating ...")

    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        dotenv_path.touch()
    # check these options
    edwh.check_env(
        key="HOSTINGDOMAIN",
        default="localhost",
        comment="hostname like meteddie.nl; edwh.nl; localhost; robin.edwh.nl",
    )
    edwh.check_env(
        key="APPLICATION_NAME",
        default="logs",
        comment="used for routing traefik. [www.]<applicationname>.<hostingdomain>, "
        "main application name, also used for registring treafik settings.",
    )
    edwh.check_env(
        key="CERTRESOLVER",
        default="letsencrypt",
        comment="which certresolver to use - default|staging|letsencrypt. See reverse proxy setup for options",
    )
    edwh.set_env_value(
        dotenv_path, "SCHEMA_VERSION", edwh.tasks.calculate_schema_hash()
    )
    edwh.check_env(
        key="WEB2PY_PASSWORD",
        default=edwh.tasks.generate_password(c, silent=True),
        comment="password for web2py",
    )

    # chown all files to 1050:1050 in the app folder
    print("Chowning files to microservices:microservices in app folder")
    c.run("sudo chown -R 1050:1050 web2py/app")
