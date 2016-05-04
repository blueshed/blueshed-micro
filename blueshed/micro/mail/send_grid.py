import sendgrid
import os
import urllib
from tornado.options import options, define
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

define("sendgriduser", default=None, help="sendgrid username")
define("sendgridpass", default=None, help="sendgrid password")


def send(to_addr, from_addr, subject, body, html=None):
    username = os.environ.get("SENDGRID_USERNAME", options.sendgriduser)
    password = os.environ.get("SENDGRID_PASSWORD", options.sendgridpass)
    sg = sendgrid.SendGridClient(username, password)

    message = sendgrid.Mail()
    message.add_to(to_addr)
    message.set_subject(subject)
    message.set_text(body)
    if html:
        message.set_html(html)
    message.set_from(from_addr)
    status, msg = sg.send(message)

    return status, msg


def send_async(to_addr, from_addr, subject, body, html=None):
    client = AsyncHTTPClient()
    data = {
        "api_user": os.environ.get("SENDGRID_USERNAME", options.sendgriduser),
        "api_key": os.environ.get("SENDGRID_PASSWORD", options.sendgridpass),
        "to": to_addr,
        "from": from_addr,
        "subject": subject,
        "text": body
    }
    if html is not None:
        data["html"] = html
    request = HTTPRequest("https://api.sendgrid.com/api/mail.send.json",
                          method='POST',
                          body=urllib.parse.urlencode(data))
    return client.fetch(request)
