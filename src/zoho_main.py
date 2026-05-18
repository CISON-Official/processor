import smtplib
from decouple import config
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText

USERNAME = str(config("ZOHO_CAMPAIGN_USERNAME"))
PASSWORD = str(config("ZOHO_CAMPAIGN_PASSWORD"))


def send_campaign(title: str, recepient: str, msg: MIMEText):
    sender = USERNAME
    sender_title = title
    recipient = recepient

    # Create message
    # msg = MIMEText("Message text", 'plain', 'utf-8')
    # msg['Subject'] =  Header("Sent from python", 'utf-8')
    # msg['From'] = formataddr((str(Header(sender_title, 'utf-8')), sender))
    # msg['To'] = recipient

    # Create server object with SSL option
    # Change below smtp.zoho.com, corresponds to your location in the world.
    # For instance smtp.zoho.eu if you are in Europe or smtp.zoho.in if you are in India.
    server = smtplib.SMTP_SSL("smtp.zoho.com", 465)

    # Perform operations via server
    server.login(sender, PASSWORD)
    server.sendmail(sender, [recipient], msg.as_string())
    server.quit()
