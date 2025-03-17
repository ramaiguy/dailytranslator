from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class DeliveryMethod(Enum):
    """Method for delivering text portions to users."""
    EMAIL = "email"
    SMS = "sms"


@dataclass
class TextSource:
    """A source text that requires translation."""
    id: str  # Unique identifier
    title: str
    file_path: str  # Path to the full text file
    language: str  # Source language
    target_language: str  # Target language for translation
    author: Optional[str] = None
    sentences_per_day: int = 3  # Number of sentences to send per day
    sentences: List[str] = field(default_factory=list)  # Parsed sentences from the text
    
    def total_days(self) -> int:
        """Calculate the total number of days needed to translate this text."""
        return (len(self.sentences) + self.sentences_per_day - 1) // self.sentences_per_day


@dataclass
class User:
    """A user who translates texts."""
    id: str  # Unique identifier
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_method: DeliveryMethod = DeliveryMethod.EMAIL
    
    def __post_init__(self):
        # Validate that we have the appropriate contact info for the preferred method
        if self.preferred_method == DeliveryMethod.EMAIL and not self.email:
            raise ValueError("Email address is required for email delivery")
        if self.preferred_method == DeliveryMethod.SMS and not self.phone:
            raise ValueError("Phone number is required for SMS delivery")


@dataclass
class TranslationProgress:
    """Tracks a user's progress in translating a specific text."""
    user_id: str
    text_id: str
    current_position: int = 0  # Current sentence index
    last_sent_date: Optional[datetime] = None
    translations: Dict[int, str] = field(default_factory=dict)  # Maps sentence index to translation
    
    @property
    def is_complete(self) -> bool:
        """Check if the translation is complete."""
        return len(self.translations) >= self.current_position
    
    @property
    def completion_percentage(self) -> float:
        """Calculate the percentage of completion."""
        if not hasattr(self, '_total_sentences'):
            return 0.0
        return (len(self.translations) / self._total_sentences) * 100
    
    def set_total_sentences(self, total: int) -> None:
        """Set the total number of sentences in the text."""
        self._total_sentences = total
