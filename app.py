#!/usr/bin/env python3
import argparse
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

from config import Config
from models import User, TextSource, DeliveryMethod
from text_manager import TextManager
from user_manager import UserManager
from messaging import MessagingService
from translation_assembler import TranslationAssembler


class TranslationServiceApp:
    """Main application for the text translation service."""
    
    def __init__(self):
        """Initialize the translation service application."""
        # Create required directories
        Config.create_directories()
        
        # Initialize components
        self.text_manager = TextManager(data_dir=Config.TEXTS_DIR)
        self.user_manager = UserManager()
        
        # Set up messaging service with config
        email_config = {
            'host': Config.EMAIL_HOST,
            'port': Config.EMAIL_PORT,
            'username': Config.EMAIL_HOST_USER,
            'password': Config.EMAIL_HOST_PASSWORD,
            'use_tls': Config.EMAIL_USE_TLS
        }
        
        sms_config = {
            'account_sid': Config.SMS_ACCOUNT_SID,
            'auth_token': Config.SMS_AUTH_TOKEN,
            'from_number': Config.SMS_FROM_NUMBER
        }
        
        self.messaging = MessagingService(
            email_config=email_config,
            sms_config=sms_config,
            reply_email=Config.REPLY_TO_EMAIL
        )
        
        self.assembler = TranslationAssembler(output_dir=Config.TRANSLATED_DIR)
    
    def register_text(self, file_path: str, title: str, **kwargs) -> TextSource:
        """
        Register a new text for translation.
        
        Args:
            file_path: Path to the text file
            title: Title of the text
            **kwargs: Additional arguments for TextSource
            
        Returns:
            The registered TextSource object
        """
        # Generate an ID if not provided
        text_id = kwargs.get('id', self._generate_id(title))
        
        # Register the text
        return self.text_manager.register_text(
            id=text_id,
            title=title,
            file_path=file_path,
            language=kwargs.get('language', 'en'),
            target_language=kwargs.get('target_language', 'es'),
            author=kwargs.get('author'),
            sentences_per_day=kwargs.get('sentences_per_day', Config.DEFAULT_SENTENCES_PER_DAY)
        )
    
    def register_user(self, name: str, **kwargs) -> User:
        """
        Register a new user.
        
        Args:
            name: User's name
            **kwargs: Additional arguments for User
            
        Returns:
            The registered User object
        """
        # Generate an ID if not provided
        user_id = kwargs.get('id', self._generate_id(name))
        
        # Determine delivery method
        if 'preferred_method' in kwargs:
            method = kwargs['preferred_method']
        elif kwargs.get('email') and not kwargs.get('phone'):
            method = DeliveryMethod.EMAIL
        elif kwargs.get('phone') and not kwargs.get('email'):
            method = DeliveryMethod.SMS
        else:
            method = DeliveryMethod.EMAIL  # Default
        
        # Register the user
        return self.user_manager.register_user(
            id=user_id,
            name=name,
            email=kwargs.get('email'),
            phone=kwargs.get('phone'),
            preferred_method=method
        )
    
    def assign_text_to_user(self, user_id: str, text_id: str) -> None:
        """
        Assign a text to a user for translation.
        
        Args:
            user_id: ID of the user
            text_id: ID of the text
        """
        # Get the text to find out how many sentences it has
        text = self.text_manager.get_text(text_id)
        total_sentences = len(text.sentences)
        
        # Assign the text to the user
        self.user_manager.assign_text(user_id, text_id, total_sentences)
        
        print(f"Assigned text '{text.title}' to user '{self.user_manager.get_user(user_id).name}'")
        print(f"The text has {total_sentences} sentences, which will take approximately " +
              f"{text.total_days()} days to translate at {text.sentences_per_day} sentences per day.")
    
    def send_daily_portions(self, user_ids: Optional[List[str]] = None) -> None:
        """
        Send daily portions to users.
        
        Args:
            user_ids: Optional list of user IDs to send to. If None, send to all users.
        """
        now = datetime.now()
        users_to_process = user_ids or list(self.user_manager.users.keys())
        
        for user_id in users_to_process:
            user = self.user_manager.get_user(user_id)
            
            # Get all progress objects for this user
            for progress in self.user_manager.progress[user_id]:
                text_id = progress.text_id
                
                try:
                    # Get the text
                    text = self.text_manager.get_text(text_id)
                    
                    # Skip if we've sent all sentences
                    if progress.current_position >= len(text.sentences):
                        print(f"User {user.name} has completed all sentences for {text.title}")
                        continue
                    
                    # Get sentences for today
                    start_position = progress.current_position
                    sentences = self.text_manager.get_daily_portion(text_id, start_position)
                    sentence_indices = list(range(start_position, start_position + len(sentences)))
                    
                    # Send the sentences
                    result = self.messaging.send_daily_portion(
                        user=user,
                        text_title=text.title,
                        sentences=sentences,
                        sentence_indices=sentence_indices
                    )
                    
                    if result:
                        # Update progress
                        self.user_manager.update_progress(
                            user_id=user_id,
                            text_id=text_id,
                            position=start_position + len(sentences),
                            sent_date=now
                        )
                        print(f"Sent {len(sentences)} sentences from '{text.title}' to {user.name}")
                    else:
                        print(f"Failed to send sentences to {user.name}")
                        
                except Exception as e:
                    print(f"Error sending to user {user_id} for text {text_id}: {str(e)}")
    
    def process_translation_reply(self, sender: str, subject: str, body: str) -> None:
        """
        Process a reply containing translations.
        
        Args:
            sender: Email address or phone number of the sender
            subject: Subject of the message
            body: Body of the message containing translations
        """
        # Find the user based on email or phone
        user_id = None
        for uid, user in self.user_manager.users.items():
            if user.email == sender or user.phone == sender:
                user_id = uid
                break
        
        if not user_id:
            print(f"Unknown sender: {sender}")
            return
        
        # Extract text_id from subject if possible (format: "Daily Translation: {text_title}")
        text_id = None
        if subject.startswith("Daily Translation:"):
            text_title = subject[len("Daily Translation:"):].strip()
            # Find text with matching title
            for tid, text in self.text_manager.texts.items():
                if text.title == text_title:
                    text_id = tid
                    break
        
        if not text_id:
            # If we can't determine the text, use the first one assigned to the user
            if self.user_manager.progress[user_id]:
                text_id = self.user_manager.progress[user_id][0].text_id
            else:
                print(f"Could not determine which text user {user_id} is translating")
                return
        
        # Parse the translations from the reply
        translations = self.messaging.process_reply(sender, subject, body)
        
        if not translations:
            print(f"No translations found in reply from {sender}")
            return
        
        # Get the user's current progress
        progress = self.user_manager.get_progress(user_id, text_id)
        
        # Convert relative indices in the translation to absolute indices in the text
        # The user is replying to sentences starting at (current_position - num_sentences_last_sent)
        # We need to determine this starting position
        text = self.text_manager.get_text(text_id)
        sentences_per_day = text.sentences_per_day
        
        # Assuming the user is replying to the most recent sentences
        start_position = max(0, progress.current_position - sentences_per_day)
        
        # Save each translation
        for rel_idx, translation in translations.items():
            abs_idx = start_position + rel_idx
            
            # Save in user's progress
            self.user_manager.save_translation(user_id, text_id, abs_idx, translation)
            
            # Also save in the text manager
            self.text_manager.save_translated_sentence(text_id, abs_idx, translation)
        
        print(f"Saved {len(translations)} translations from {self.user_manager.get_user(user_id).name} for '{text.title}'")
    
    def generate_translation_file(self, text_id: str, output_format: str = "txt") -> str:
        """
        Generate a translation file from all available translations.
        
        Args:
            text_id: ID of the text
            output_format: Format for the output file (txt, json, etc.)
            
        Returns:
            Path to the generated translation file
        """
        # Get the text
        text = self.text_manager.get_text(text_id)
        
        # Get all translations for this text
        translations = self.user_manager.get_all_translations(text_id)
        
        # Generate the file
        output_path = self.assembler.assemble_translation(
            text_source=text,
            translations=translations,
            output_format=output_format
        )
        
        # Get status
        status = self.assembler.get_translation_status(text, translations)
        
        print(f"Generated translation file for '{text.title}'")
        print(f"Completion: {status['completion_percentage']:.1f}% ({status['translated_sentences']}/{status['total_sentences']} sentences)")
        print(f"Output file: {output_path}")
        
        return output_path
    
    def _generate_id(self, name: str) -> str:
        """
        Generate a simple ID from a name.
        
        Args:
            name: Name to generate ID from
            
        Returns:
            A simple ID string
        """
        # Convert to lowercase, replace spaces with underscores, remove non-alphanumeric
        id_base = "".join(c for c in name.lower().replace(" ", "_") if c.isalnum() or c == "_")
        
        # Add timestamp to ensure uniqueness
        timestamp = int(time.time())
        return f"{id_base}_{timestamp}"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Text Translation Service")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Register text command
    text_parser = subparsers.add_parser("register_text", help="Register a new text for translation")
    text_parser.add_argument("file_path", help="Path to the text file")
    text_parser.add_argument("title", help="Title of the text")
    text_parser.add_argument("--author", help="Author of the text")
    text_parser.add_argument("--language", default="en", help="Source language code")
    text_parser.add_argument("--target-language", default="es", help="Target language code")
    text_parser.add_argument("--sentences-per-day", type=int, default=Config.DEFAULT_SENTENCES_PER_DAY, 
                           help="Number of sentences to send per day")
    
    # Register user command
    user_parser = subparsers.add_parser("register_user", help="Register a new user")
    user_parser.add_argument("name", help="User's name")
    user_parser.add_argument("--email", help="User's email address")
    user_parser.add_argument("--phone", help="User's phone number")
    user_parser.add_argument("--preferred-method", choices=["email", "sms"], default="email",
                           help="Preferred delivery method")
    
    # Assign text command
    assign_parser = subparsers.add_parser("assign_text", help="Assign a text to a user")
    assign_parser.add_argument("user_id", help="ID of the user")
    assign_parser.add_argument("text_id", help="ID of the text")
    
    # Send daily portions command
    send_parser = subparsers.add_parser("send_daily", help="Send daily portions to users")
    send_parser.add_argument("--users", nargs="*", help="Optional list of user IDs to send to")
    
    # Process reply command
    reply_parser = subparsers.add_parser("process_reply", help="Process a translation reply")
    reply_parser.add_argument("sender", help="Email address or phone number of the sender")
    reply_parser.add_argument("subject", help="Subject of the message")
    reply_parser.add_argument("body", help="Body of the message containing translations")
    
    # Generate translation file command
    generate_parser = subparsers.add_parser("generate", help="Generate a translation file")
    generate_parser.add_argument("text_id", help="ID of the text")
    generate_parser.add_argument("--format", choices=["txt", "json"], default="txt",
                              help="Output format")
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()
    app = TranslationServiceApp()
    
    if args.command == "register_text":
        text = app.register_text(
            file_path=args.file_path,
            title=args.title,
            author=args.author,
            language=args.language,
            target_language=args.target_language,
            sentences_per_day=args.sentences_per_day
        )
        print(f"Registered text: {text.title} (ID: {text.id})")
        print(f"Total sentences: {len(text.sentences)}")
        
    elif args.command == "register_user":
        method = DeliveryMethod.EMAIL if args.preferred_method == "email" else DeliveryMethod.SMS
        user = app.register_user(
            name=args.name,
            email=args.email,
            phone=args.phone,
            preferred_method=method
        )
        print(f"Registered user: {user.name} (ID: {user.id})")
        
    elif args.command == "assign_text":
        app.assign_text_to_user(args.user_id, args.text_id)
        
    elif args.command == "send_daily":
        app.send_daily_portions(args.users)
        
    elif args.command == "process_reply":
        app.process_translation_reply(args.sender, args.subject, args.body)
        
    elif args.command == "generate":
        app.generate_translation_file(args.text_id, args.format)
        
    else:
        print("Please specify a command. Use --help for available commands.")


if __name__ == "__main__":
    main()
