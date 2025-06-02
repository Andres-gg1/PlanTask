import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailSender:
    def send_email(self, subject, body, to_email, html_body=None):
        raise NotImplementedError()

class SMTPEmailSender(EmailSender):
    def __init__(self, host, port, username, password, from_email):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email

    def send_email(self, subject, body, to_email, html_body=None):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email

        part1 = MIMEText(body, "plain")
        msg.attach(part1)

        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
        except Exception as e:
            print(f"[ERROR IN SEND_EMAIL] there was an error: {e}")
