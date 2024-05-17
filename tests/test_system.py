import subprocess
import pytest
import sqlite3


def test_docker_containers_running():
    """
    Test if the required Docker containers are running; docker-logger-web2py and logger
    """
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True
    )
    running_containers = result.stdout.splitlines()

    # test if the docker-logger-web2py is running
    assert (
        "docker-logger-web2py-1" in running_containers
    ), "docker-logger-web2py container is not running"

    # test if the logger is running
    assert "logger" in running_containers, "logger container is not running"


def test_database_connection():
    """
    Test if the web2py database connection is working
    """
    try:
        connection = sqlite3.connect("../web2py/app/databases/storage.sqlite")
        cur = connection.cursor()
        cur.execute("SELECT * FROM auth_user;")
        cur.close()
        connection.close()

    # if the database connection fails, fail the test
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
