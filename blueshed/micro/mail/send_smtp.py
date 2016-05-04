from tornado.options import define, options
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


define("mailhost", default=None, help="smtp host for logging")
define("mailport", default=smtplib.SMTP_PORT, type=int, help="smtp host port")
define("mailusername", default=None, help="smtp username")
define("mailpassword", default=None, help="smtp password")
define("mailsecure", default=False, type=bool, help="smtp secure")


def send(to_addr, from_addr, subject, body, html=None):

    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, "plain"))
    if html is not None:
        msg.attach(MIMEText(html, "html"))

    smtp = smtplib.SMTP(options.mailhost, options.mailport)

    if options.mailsecure is True:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

    if options.mailusername:
        smtp.login(options.mailusername, options.mailpassword)

    smtp.sendmail(from_addr, to_addr, msg.as_string())

    smtp.quit()
