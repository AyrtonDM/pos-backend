# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

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


def send_password_recovery_email(
    email: str,
    nombre: str,
    nueva_contrasena: str,
) -> bool:
    """
    Envia un email con una nueva contrasena temporal.
    """
    try:
        subject = "Recuperacion de contrasena - POS System"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Hola, {nombre}</h2>
                    <p style="color: #666;">Recibimos una solicitud para recuperar tu contrasena.</p>
                    <p style="color: #666;">Tu nueva contrasena es:</p>
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #007bff; margin: 0;">{nueva_contrasena}</h1>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        Inicia sesion con esta contrasena y cambiala lo antes posible.
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        Si no solicitaste esta recuperacion, contacta al administrador.
                    </p>
                </div>
            </body>
        </html>
        """

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = MAIL_FROM
        message["To"] = email

        text_content = (
            "Recibimos una solicitud para recuperar tu contrasena.\n"
            f"Tu nueva contrasena es: {nueva_contrasena}\n"
            "Inicia sesion con esta contrasena y cambiala lo antes posible."
        )
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)

        return True
    except Exception as e:
        print(f"Error sending password recovery email: {e}")
        return False


def send_employee_invitation_email(
    email: str,
    nombre: str,
    invitation_link: str,
) -> bool:
    """
    Envia un email con el link de invitacion a una sucursal.
    """
    try:
        subject = "Invitacion a sucursal - POS System"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Hola, {nombre}</h2>
                    <p style="color: #666;">Recibiste una invitacion para unirte como empleado.</p>
                    <p style="color: #666;">Para aceptar la invitacion, ingresa al siguiente link:</p>
                    <p style="margin: 20px 0;">
                        <a href="{invitation_link}" style="background-color: #007bff; color: white; padding: 12px 16px; text-decoration: none; border-radius: 5px;">
                            Aceptar invitacion
                        </a>
                    </p>
                    <p style="color: #666; font-size: 12px;">Si el boton no funciona, copia y pega este link en tu navegador:</p>
                    <p style="color: #007bff; font-size: 12px;">{invitation_link}</p>
                </div>
            </body>
        </html>
        """

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = MAIL_FROM
        message["To"] = email

        text_content = (
            "Recibiste una invitacion para unirte como empleado.\n"
            f"Acepta la invitacion aqui: {invitation_link}"
        )
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)

        return True
    except Exception as e:
        print(f"Error sending employee invitation email: {e}")
        return False


def send_client_invitation_email(
    email: str,
    nombre: str,
    empresa_nombre: str,
    invitation_link: str,
) -> bool:
    """
    Envia un email con el link de invitacion para ser cliente de una empresa.
    """
    try:
        subject = f"Invitacion para ser cliente de {empresa_nombre} - POS System"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);">
                    <h2 style="color: #333; margin-top: 0;">Hola, {nombre}</h2>
                    <p style="color: #666; line-height: 1.6;">Recibiste una invitacion para convertirte en cliente de <strong>{empresa_nombre}</strong>.</p>
                    <p style="color: #666; line-height: 1.6;">Para aceptar la invitacion y confirmar tu relacion con la empresa, haz clic en el siguiente boton:</p>
                    <p style="margin: 28px 0; text-align: center;">
                        <a href="{invitation_link}" style="background-color: #007bff; color: white; padding: 12px 18px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                            Aceptar invitacion
                        </a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-bottom: 6px;">Si el boton no funciona, copia y pega este link en tu navegador:</p>
                    <p style="color: #007bff; font-size: 12px; word-break: break-all;">{invitation_link}</p>
                </div>
            </body>
        </html>
        """

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = MAIL_FROM
        message["To"] = email

        text_content = (
            f"Recibiste una invitacion para convertirte en cliente de {empresa_nombre}.\n"
            f"Acepta la invitacion aqui: {invitation_link}"
        )
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)

        return True
    except Exception as e:
        print(f"Error sending client invitation email: {e}")
        return False


def send_invoice_email(
    email: str,
    nombre: str,
    numero_factura: int,
    pdf_path: Path,
) -> bool:
    try:
        message = MIMEMultipart()
        message["Subject"] = f"Factura N. {numero_factura} - POS System"
        message["From"] = MAIL_FROM
        message["To"] = email
        message.attach(
            MIMEText(
                f"Hola, {nombre}.\nAdjuntamos la factura N. {numero_factura} de tu compra.",
                "plain",
            )
        )

        with pdf_path.open("rb") as archivo:
            adjunto = MIMEApplication(archivo.read(), _subtype="pdf")
        adjunto.add_header(
            "Content-Disposition",
            "attachment",
            filename=pdf_path.name,
        )
        message.attach(adjunto)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending invoice email: {e}")
        return False
