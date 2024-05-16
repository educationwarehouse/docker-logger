import bcrypt
import os
from app.controllers.default import verify_password, manipulate_url, string_to_color


def test_verify_password():
    """
    Test the verify_password function with a correct and incorrect password
    """
    hashed_correct_password = bcrypt.hashpw(
        "correct_password".encode("utf-8"), bcrypt.gensalt()
    )

    # test the correct password
    assert (
        verify_password("correct_password", hashed_correct_password.decode("utf-8"))
        == True
    )

    # test an incorrect password
    assert (
        verify_password("incorrect_password", hashed_correct_password.decode("utf-8"))
        == False
    )


def test_manipulate_url():
    """
    Test the manipulate_url function with adding, modifying and removing parameters
    """
    hosting_domain = os.getenv("HOSTING_DOMAIN")
    url = f"https://logs.{hosting_domain}/init/default/logs?param1=value1&param2=value2"

    # test adding a new parameter
    new_url = manipulate_url(url, "param3", ["value3"])
    assert "param3=value3" in new_url

    # test modifying an existing parameter
    modified_url = manipulate_url(url, "param1", ["new_value1"])
    assert "param1=new_value1" in modified_url

    # test removing a parameter
    removed_url = manipulate_url(url, "param1", None)
    assert "param1=value1" not in removed_url


def test_string_to_color():
    """
    Test the string_to_color function with a `test_string`
    """
    result = string_to_color("test_string")

    # test the length of the result; it should be 7 characters including '#'
    assert len(result) == 7

    # test if the result starts with '#'
    assert result[0] == "#"

    # test if the remaining characters are hex digits
    assert all(color in "0123456789abcdef" for color in result[1:])
