import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

msg = EmailMessage()
msg['Subject'] = 'Test Email'
msg['From'] = EMAIL_ADDRESS
msg['To'] = EMAIL_ADDRESS  # Sends an email to yourself
msg.set_content('This is a test email.')

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Test email sent successfully!")
except Exception as e:
    print("Error sending test email:", e)