import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USER = "shar.mila.brn@gmail.com"
EMAIL_PASSWORD = "kfnb xgft royu vwld"


def send_email(to_email, subject, message):

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)

    server.sendmail(EMAIL_USER, to_email, msg.as_string())

    server.quit()

    return True