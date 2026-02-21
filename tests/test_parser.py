import pytest
from src.main import clean, get_body
from email.message import EmailMessage

def test_clean():
    assert clean("Hello World!") == "Hello_World_"
    assert clean("Email: 123") == "Email__123"
    assert clean("normal_text") == "normal_text"

def test_get_body_simple():
    msg = EmailMessage()
    msg.set_content("This is a test body")
    # EmailMessage set_content makes it non-multipart by default if it's just text
    assert get_body(msg).strip() == "This is a test body"

def test_get_body_multipart():
    msg = EmailMessage()
    msg.add_alternative("This is text", subtype='plain')
    msg.add_alternative("<h1>This is html</h1>", subtype='html')
    # get_body should pick the text/plain part
    assert get_body(msg).strip() == "This is text"

def test_get_body_html_only():

    msg = EmailMessage()

    msg.add_alternative("<h1>This is html</h1>", subtype='html')

    # Should convert to markdown

    body = get_body(msg)

    assert "This is html" in body

    # It might use # or setext style (=====)

    assert "#" in body or "====" in body
