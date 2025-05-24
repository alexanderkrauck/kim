"""
Email utility functions for sending outreach emails
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from .firebase_utils import get_smtp_settings
from utils.logging_config import get_logger

logger = get_logger(__file__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self, use_env: bool = False):
        """
        Initialize email service
        
        Args:
            use_env: If True, use environment variables for SMTP settings
        """
        self.smtp_settings = get_smtp_settings(use_env)
        self.smtp_server = None
    
    def connect(self):
        """Establish SMTP connection"""
        try:
            if self.smtp_settings.get('secure'):
                self.smtp_server = smtplib.SMTP_SSL(
                    self.smtp_settings['host'], 
                    self.smtp_settings['port']
                )
            else:
                self.smtp_server = smtplib.SMTP(
                    self.smtp_settings['host'], 
                    self.smtp_settings['port']
                )
                self.smtp_server.starttls()
            
            self.smtp_server.login(
                self.smtp_settings['username'],
                self.smtp_settings['password']
            )
            
            logger.info("SMTP connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            return False
    
    def disconnect(self):
        """Close SMTP connection"""
        if self.smtp_server:
            try:
                self.smtp_server.quit()
                logger.info("SMTP connection closed")
            except Exception as e:
                logger.error(f"Error closing SMTP connection: {e}")
    
    def send_email(self,
                   to_email: str,
                   subject: str,
                   content: str,
                   to_name: str = None,
                   reply_to: str = None) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (HTML or plain text)
            to_name: Recipient name (optional)
            reply_to: Reply-to email address (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_settings['fromName']} <{self.smtp_settings['fromEmail']}>"
            
            if to_name:
                msg['To'] = f"{to_name} <{to_email}>"
            else:
                msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            elif self.smtp_settings.get('replyToEmail'):
                msg['Reply-To'] = self.smtp_settings['replyToEmail']
            
            # Add content
            if content.strip().startswith('<'):
                # HTML content
                html_part = MIMEText(content, 'html')
                msg.attach(html_part)
            else:
                # Plain text content
                text_part = MIMEText(content, 'plain')
                msg.attach(text_part)
            
            # Send email
            if not self.smtp_server:
                if not self.connect():
                    return False
            
            self.smtp_server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_bulk_emails(self, email_list: List[Dict]) -> Dict[str, int]:
        """
        Send multiple emails
        
        Args:
            email_list: List of email dictionaries with keys:
                       'to_email', 'subject', 'content', 'to_name' (optional)
                       
        Returns:
            Dictionary with 'sent' and 'failed' counts
        """
        results = {'sent': 0, 'failed': 0}
        
        if not self.connect():
            logger.error("Failed to establish SMTP connection for bulk emails")
            return results
        
        try:
            for email_data in email_list:
                success = self.send_email(
                    to_email=email_data['to_email'],
                    subject=email_data['subject'],
                    content=email_data['content'],
                    to_name=email_data.get('to_name'),
                    reply_to=email_data.get('reply_to')
                )
                
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    
        finally:
            self.disconnect()
        
        logger.info(f"Bulk email results: {results['sent']} sent, {results['failed']} failed")
        return results
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.connect():
            self.disconnect()
            return True
        return False


def format_email_content(content: str, lead_data: Dict) -> str:
    """
    Format email content with lead data placeholders
    
    Args:
        content: Email content with placeholders
        lead_data: Lead data for replacement
        
    Returns:
        Formatted email content
    """
    # Replace common placeholders
    replacements = {
        '{name}': lead_data.get('name', 'there'),
        '{first_name}': lead_data.get('name', 'there').split()[0] if lead_data.get('name') else 'there',
        '{company}': lead_data.get('company', 'your company'),
        '{email}': lead_data.get('email', ''),
    }
    
    formatted_content = content
    for placeholder, value in replacements.items():
        formatted_content = formatted_content.replace(placeholder, value)
    
    return formatted_content


def create_email_signature(from_name: str, company_name: str = None) -> str:
    """
    Create a professional email signature
    
    Args:
        from_name: Name of the sender
        company_name: Company name (optional)
        
    Returns:
        HTML email signature
    """
    signature = f"""
    <br><br>
    Best regards,<br>
    <strong>{from_name}</strong>
    """
    
    if company_name:
        signature += f"<br>{company_name}"
    
    return signature 