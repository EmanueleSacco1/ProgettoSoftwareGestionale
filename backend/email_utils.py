import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(recipient_email, subject, body, smtp_config, attachment_path=None):
    """
    Connects to an SMTP server and sends an email.
    
    Can optionally attach one file.

    Args:
        recipient_email (str): The 'To' email address.
        subject (str): The email subject line.
        body (str): The plain text email body.
        smtp_config (dict): A dictionary containing 'host', 'port', 'user', 'password'.
        attachment_path (str, optional): The full local path to a file to attach.

    Returns:
        tuple (bool, str): (True, "Email sent successfully.") on success,
                           (False, "Failed to send email: [error]") on failure.
    """
    # Check for minimum configuration
    if not smtp_config.get('host') or not smtp_config.get('user') or not smtp_config.get('password'):
        return False, "SMTP configuration (host, user, password) incomplete."

    try:
        # Create the email message object
        msg = MIMEMultipart()
        msg['From'] = smtp_config['user']
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach the body as plain text
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach the file (if provided and exists)
        if attachment_path and os.path.exists(attachment_path):
            filename = os.path.basename(attachment_path)
            # Open the file in read-binary mode
            with open(attachment_path, "rb") as attachment:
                # Create the attachment part
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            # Encode file in base64 for email transport
            encoders.encode_base64(part)
            
            # Add the necessary header
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}',
            )
            # Attach the part to the message
            msg.attach(part)
        
        # Connect to the SMTP server
        # The port is expected to be an integer
        smtp_port = int(smtp_config.get('port', 587))
        server = smtplib.SMTP(smtp_config['host'], smtp_port)
        server.starttls() # Secure the connection
        server.login(smtp_config['user'], smtp_config['password'])
        text = msg.as_string()
        
        # Send the email
        server.sendmail(smtp_config['user'], recipient_email, text)
        server.quit()
        
        return True, "Email sent successfully."

    except Exception as e:
        return False, f"Failed to send email: {e}"