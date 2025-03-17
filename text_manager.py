import os
import re
import nltk
from typing import List, Optional

from models import TextSource


class TextManager:
    """Manages text sources, parsing, and segmentation."""
    
    def __init__(self, data_dir: str = "data/texts"):
        """
        Initialize the TextManager.
        
        Args:
            data_dir: Directory where text files are stored
        """
        self.data_dir = data_dir
        self.texts = {}  # Dictionary of TextSource objects by ID
        
        # Ensure NLTK resources are available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
    
    def register_text(self, 
                      id: str, 
                      title: str, 
                      file_path: str, 
                      language: str, 
                      target_language: str,
                      author: Optional[str] = None,
                      sentences_per_day: int = 3) -> TextSource:
        """
        Register a new text for translation.
        
        Args:
            id: Unique identifier for the text
            title: Title of the text
            file_path: Path to the text file
            language: Source language code
            target_language: Target language code
            author: Author name (optional)
            sentences_per_day: Number of sentences to send per day
            
        Returns:
            The created TextSource object
        """
        if id in self.texts:
            raise ValueError(f"Text with ID '{id}' already exists")
            
        # Ensure file exists
        full_path = os.path.join(self.data_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Text file not found: {full_path}")
            
        text_source = TextSource(
            id=id,
            title=title,
            author=author,
            file_path=file_path,
            language=language,
            target_language=target_language,
            sentences_per_day=sentences_per_day
        )
        
        # Parse the text into sentences
        text_source.sentences = self._parse_text(full_path)
        
        # Store the text source
        self.texts[id] = text_source
        return text_source
    
    def get_text(self, text_id: str) -> TextSource:
        """
        Get a text source by ID.
        
        Args:
            text_id: ID of the text to retrieve
            
        Returns:
            The TextSource object
        """
        if text_id not in self.texts:
            raise KeyError(f"Text with ID '{text_id}' not found")
        return self.texts[text_id]
    
    def get_daily_portion(self, text_id: str, position: int) -> List[str]:
        """
        Get a daily portion of sentences from a text.
        
        Args:
            text_id: ID of the text
            position: Starting position (sentence index)
            
        Returns:
            List of sentences for the day
        """
        text_source = self.get_text(text_id)
        start_idx = position
        end_idx = min(start_idx + text_source.sentences_per_day, len(text_source.sentences))
        return text_source.sentences[start_idx:end_idx]
    
    def _parse_text(self, file_path: str) -> List[str]:
        """
        Parse a text file into sentences.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of sentences
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            
        # Clean the text (remove extra whitespace, etc.)
        text = re.sub(r'\s+', ' ', text)
        
        # Use NLTK to split text into sentences
        sentences = nltk.sent_tokenize(text)
        
        # Filter out empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def save_translated_sentence(self, text_id: str, sentence_index: int, translation: str) -> None:
        """
        Save a translated sentence.
        
        Args:
            text_id: ID of the text
            sentence_index: Index of the sentence in the text
            translation: Translated text
        """
        # This would typically write to a database or file
        # For now, we'll just print to demonstrate
        text = self.get_text(text_id)
        print(f"Saved translation for {text.title}, sentence {sentence_index}:")
        print(f"Original: {text.sentences[sentence_index]}")
        print(f"Translation: {translation}")
        
    def export_translations(self, text_id: str, translations: dict) -> str:
        """
        Export all translations for a text to a new file.
        
        Args:
            text_id: ID of the text
            translations: Dictionary mapping sentence indices to translations
            
        Returns:
            Path to the created translation file
        """
        text = self.get_text(text_id)
        output_path = os.path.join(
            self.data_dir, 
            f"{os.path.splitext(text.file_path)[0]}_translated_{text.target_language}.txt"
        )
        
        with open(output_path, 'w', encoding='utf-8') as file:
            for i, sentence in enumerate(text.sentences):
                if i in translations:
                    file.write(f"{translations[i]}\n")
                else:
                    # Mark untranslated sentences
                    file.write(f"[UNTRANSLATED: {sentence}]\n")
                    
        return output_path
