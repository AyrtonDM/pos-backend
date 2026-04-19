# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")


def send_verification_email(email: str, nombre: str, codigo_verificacion: str) -> bool:
    """
    Envia un email con el codigo de verificacion.
    """
    try:
        subject = "Codigo de verificacion - POS System"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Bienvenido, {nombre}!</h2>
                    <p style="color: #666;">Para verificar tu correo electronico y activar tu cuenta, usa el siguiente codigo:</p>
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #007bff; letter-spacing: 5px; margin: 0;">{codigo_verificacion}</h1>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        Este codigo expira en 15 minutos. No compartas este codigo con nadie.
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        Si no solicitaste esta verificacion, ignora este email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = MAIL_FROM
        message["To"] = email
        
        # Adjuntar version en texto plano como alternativa
        text_content = f"Tu codigo de verificacion es: {codigo_verificacion}\nExpira en 15 minutos."
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
