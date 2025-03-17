import smtplib
import os
from email.message import EmailMessage
from typing import List, Dict, Optional
from datetime import datetime
import re

from models import User, DeliveryMethod


class MessagingService:
    """Handles sending and receiving messages via email or SMS."""
    
    def __init__(self, 
                 email_config: Dict = None, 
                 sms_config: Dict = None,
                 reply_email: str = None):
        """
        Initialize the MessagingService.
        
        Args:
            email_config: Configuration for email service
            sms_config: Configuration for SMS service
            reply_email: Email address where users should send their translations
        """
        self.email_config = email_config or {}
        self.sms_config = sms_config or {}
        self.reply_email = reply_email
        
        # Set up a basic logging mechanism
        self.message_log = []
    
    def send_daily_portion(self, 
                          user: User, 
                          text_title: str, 
                          sentences: List[str], 
                          sentence_indices: List[int]) -> bool:
        """
        Send a daily portion of sentences to a user.
        
        Args:
            user: The user to send to
            text_title: Title of the text being translated
            sentences: List of sentences to send
            sentence_indices: Indices of the sentences in the original text
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        if user.preferred_method == DeliveryMethod.EMAIL:
            return self._send_email(user, text_title, sentences, sentence_indices)
        elif user.preferred_method == DeliveryMethod.SMS:
            return self._send_sms(user, text_title, sentences, sentence_indices)
        else:
            raise ValueError(f"Unsupported delivery method: {user.preferred_method}")
    
    def _send_email(self, 
                   user: User, 
                   text_title: str, 
                   sentences: List[str], 
                   sentence_indices: List[int]) -> bool:
        """
        Send sentences via email.
        
        Args:
            user: The user to send to
            text_title: Title of the text being translated
            sentences: List of sentences to send
            sentence_indices: Indices of the sentences in the original text
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        if not user.email:
            raise ValueError(f"User {user.id} does not have an email address")
        
        # Create the email content
        subject = f"Daily Translation: {text_title}"
        body = self._format_message_body(text_title, sentences, sentence_indices)
        
        # In a real implementation, this would send an actual email
        # For demonstration purposes, we'll just log it
        log_entry = {
            'timestamp': datetime.now(),
            'method': 'email',
            'recipient': user.email,
            'subject': subject,
            'body': body
        }
        self.message_log.append(log_entry)
        
        print(f"Email sent to {user.name} ({user.email}):")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        
        return True
    
    def _send_sms(self, 
                 user: User, 
                 text_title: str, 
                 sentences: List[str], 
                 sentence_indices: List[int]) -> bool:
        """
        Send sentences via SMS.
        
        Args:
            user: The user to send to
            text_title: Title of the text being translated
            sentences: List of sentences to send
            sentence_indices: Indices of the sentences in the original text
            
        Returns:
            True if the SMS was sent successfully, False otherwise
        """
        if not user.phone:
            raise ValueError(f"User {user.id} does not have a phone number")
        
        # Create the SMS content (shorter for SMS)
        body = f"Translation: {text_title}\n\n"
        for i, sentence in enumerate(sentences):
            body += f"{i+1}. {sentence}\n"
        
        # For demonstration purposes, we'll just log it
        log_entry = {
            'timestamp': datetime.now(),
            'method': 'sms',
            'recipient': user.phone,
            'body': body
        }
        self.message_log.append(log_entry)
        
        print(f"SMS sent to {user.name} ({user.phone}):")
        print(f"Body:\n{body}")
        
        return True
    
    def _format_message_body(self, 
                            text_title: str, 
                            sentences: List[str], 
                            sentence_indices: List[int]) -> str:
        """
        Format the message body for email or SMS.
        
        Args:
            text_title: Title of the text being translated
            sentences: List of sentences to send
            sentence_indices: Indices of the sentences in the original text
            
        Returns:
            Formatted message body
        """
        body = f"Here are your sentences to translate from '{text_title}':\n\n"
        
        for i, (sentence, idx) in enumerate(zip(sentences, sentence_indices)):
            body += f"[{idx+1}] {sentence}\n\n"
        
        body += "To submit your translations, please reply to this message with each "
        body += "translation numbered as shown above.\n\n"
        body += "Example:\n"
        body += f"[1] Your translation of the first sentence.\n"
        body += f"[2] Your translation of the second sentence.\n"
        
        return body
    
    def process_reply(self, 
                     sender: str, 
                     subject: str, 
                     body: str) -> Dict[int, str]:
        """
        Process a reply from a user containing translations.
        
        Args:
            sender: Email address or phone number of the sender
            subject: Subject of the message (for emails)
            body: Body of the message
            
        Returns:
            Dictionary mapping sentence indices to translations
        """
        translations = {}
        
        # Parse the reply to extract translations
        # Looking for patterns like "[1] Translation text" or "1. Translation text"
        pattern = r'\[(\d+)\](.*?)(?=\[\d+\]|\Z)'
        alternative_pattern = r'(\d+)\.(.*?)(?=\d+\.|\Z)'
        
        # Try the primary pattern first
        matches = re.findall(pattern, body, re.DOTALL)
        if not matches:
            # Try the alternative pattern
            matches = re.findall(alternative_pattern, body, re.DOTALL)
        
        for idx_str, translation in matches:
            try:
                # Convert to 0-based index by subtracting 1 from user-provided number
                idx = int(idx_str) - 1
                translations[idx] = translation.strip()
            except ValueError:
                # Skip invalid indices
                continue
        
        return translations
