from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_email(buffer, filename, recipient, smtp_config):
    msg = MIMEMultipart()
    msg["Subject"] = f"Payslip for {filename}"
    msg["From"] = smtp_config["sender"]
    msg["To"] = recipient

    msg.attach(MIMEText(
        "Dear employee,\n\nPlease find your payslip attached.\n\nBest regards,\nHR Team",
        "plain"
    ))

    part = MIMEApplication(buffer, _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)

    with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
        server.starttls()
        server.login(smtp_config["user"], smtp_config["password"])
        server.send_message(msg)
