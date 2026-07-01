import os
import season
import string
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

config = wiz.model("portal/season/config")
SMTP_SENDER = config.smtp_sender
SMTP_HOST = config.smtp_host
SMTP_PORT = config.smtp_port
SMTP_PASSWORD = config.smtp_password
SMTP_BRAND_LOGO = config.smtp_brand_logo
fs = wiz.project.fs(os.path.join("config", "smtp"))

class Model:
    def __init__(self):
        pass
    
    def randomcode(self, length=6):
        string_pool = string.digits
        result = ""
        for i in range(length):
            result += random.choice(string_pool)
        return result

    def send(self, to, template=None, title="TITLE", **kwargs):
        sender = SMTP_SENDER
        if template is None:
            html = """<div style="width: 100%; min-height: 100%; background: #f5f7fb; padding-top: 48px; padding-bottom: 48px;">
    <div style="width: 80%; max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px;">
        <div style="background: #3843D0; padding: 18px 24px; border-radius: 8px; padding-bottom: 12px;">
            <img src="{brand_logo}" style="height: 36px;">
        </div>

        <div style="padding: 8px 24px; padding-bottom: 32px; padding-top: 8px;">
            <h2 style="font-size: 24px; color: #F9623E; margin-bottom: 12px;">{title}</h2>
            {message}
        </div>

        <div
            style="padding: 12px 24px; background: #2e2e2e; color: #ffffff; border-bottom-right-radius: 8px; border-bottom-left-radius: 8px; text-align: center;">
            GACHI
        </div>
    </div>
</div>"""
        else:
            html = fs.read(f"{template}.html")

        html = html.replace("{title}", title)
        html = html.replace("{brand_logo}", SMTP_BRAND_LOGO)
        for key in kwargs:
            try:
                html = html.replace("{" + key + "}", str(kwargs[key]))
            except Exception:
                pass

        msg = MIMEText(html, 'html', _charset='utf8')
        msg['Subject'] = title
        msg['From'] = SMTP_SENDER
        msg['To'] = to

        mailserver = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(SMTP_SENDER, SMTP_PASSWORD)
        mailserver.sendmail(SMTP_SENDER, to, msg.as_string())
        mailserver.quit()
    
    @classmethod
    def use(cls):
        return cls()