from typing import Dict, List, Optional
from datetime import datetime

from models import User, TranslationProgress, DeliveryMethod


class UserManager:
    """Manages users and their translation progress."""
    
    def __init__(self):
        """Initialize the UserManager."""
        self.users: Dict[str, User] = {}  # Dictionary of User objects by ID
        self.progress: Dict[str, List[TranslationProgress]] = {}  # Dictionary mapping user IDs to their translation progress
    
    def register_user(self, 
                      id: str,
                      name: str,
                      email: Optional[str] = None,
                      phone: Optional[str] = None,
                      preferred_method: DeliveryMethod = DeliveryMethod.EMAIL) -> User:
        """
        Register a new user.
        
        Args:
            id: Unique identifier for the user
            name: User's name
            email: User's email address
            phone: User's phone number
            preferred_method: User's preferred delivery method
            
        Returns:
            The created User object
        """
        if id in self.users:
            raise ValueError(f"User with ID '{id}' already exists")
        
        user = User(
            id=id,
            name=name,
            email=email,
            phone=phone,
            preferred_method=preferred_method
        )
        
        self.users[id] = user
        self.progress[id] = []
        return user
    
    def get_user(self, user_id: str) -> User:
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            The User object
        """
        if user_id not in self.users:
            raise KeyError(f"User with ID '{user_id}' not found")
        return self.users[user_id]
    
    def assign_text(self, user_id: str, text_id: str, total_sentences: int) -> TranslationProgress:
        """
        Assign a text to a user for translation.
        
        Args:
            user_id: ID of the user
            text_id: ID of the text
            total_sentences: Total number of sentences in the text
            
        Returns:
            The created TranslationProgress object
        """
        # Check if user exists
        user = self.get_user(user_id)
        
        # Check if user is already translating this text
        for progress in self.progress[user_id]:
            if progress.text_id == text_id:
                raise ValueError(f"User '{user_id}' is already translating text '{text_id}'")
        
        # Create progress tracker
        progress = TranslationProgress(
            user_id=user_id,
            text_id=text_id
        )
        progress.set_total_sentences(total_sentences)
        
        # Add to progress list
        self.progress[user_id].append(progress)
        return progress
    
    def get_progress(self, user_id: str, text_id: str) -> TranslationProgress:
        """
        Get a user's progress on a specific text.
        
        Args:
            user_id: ID of the user
            text_id: ID of the text
            
        Returns:
            The TranslationProgress object
        """
        # Check if user exists
        user = self.get_user(user_id)
        
        # Find the right progress object
        for progress in self.progress[user_id]:
            if progress.text_id == text_id:
                return progress
        
        raise ValueError(f"User '{user_id}' is not translating text '{text_id}'")
    
    def update_progress(self, user_id: str, text_id: str, position: int, sent_date: datetime) -> None:
        """
        Update a user's progress to indicate that sentences were sent.
        
        Args:
            user_id: ID of the user
            text_id: ID of the text
            position: New position (sentence index)
            sent_date: Date when sentences were sent
        """
        progress = self.get_progress(user_id, text_id)
        progress.current_position = position
        progress.last_sent_date = sent_date
    
    def save_translation(self, user_id: str, text_id: str, sentence_index: int, translation: str) -> None:
        """
        Save a translated sentence from a user.
        
        Args:
            user_id: ID of the user
            text_id: ID of the text
            sentence_index: Index of the sentence in the text
            translation: Translated text
        """
        progress = self.get_progress(user_id, text_id)
        progress.translations[sentence_index] = translation
    
    def get_all_translations(self, text_id: str) -> Dict[int, str]:
        """
        Get all translations for a text from all users.
        
        Args:
            text_id: ID of the text
            
        Returns:
            Dictionary mapping sentence indices to translations
        """
        all_translations = {}
        
        # Check all users' progress
        for user_id, progress_list in self.progress.items():
            for progress in progress_list:
                if progress.text_id == text_id:
                    # Merge this user's translations
                    all_translations.update(progress.translations)
        
        return all_translations
