import os
from typing import Dict, List, Optional
import json

from models import TextSource


class TranslationAssembler:
    """Compiles translated sentences into complete documents."""
    
    def __init__(self, output_dir: str = "data/translated"):
        """
        Initialize the TranslationAssembler.
        
        Args:
            output_dir: Directory where translated texts will be saved
        """
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def assemble_translation(self, 
                           text_source: TextSource, 
                           translations: Dict[int, str],
                           output_format: str = "txt") -> str:
        """
        Assemble translated sentences into a complete document.
        
        Args:
            text_source: The source text being translated
            translations: Dictionary mapping sentence indices to translations
            output_format: Format for the output file (txt, json, etc.)
            
        Returns:
            Path to the generated translation file
        """
        # Generate filename
        base_name = os.path.splitext(os.path.basename(text_source.file_path))[0]
        file_name = f"{base_name}_{text_source.target_language}"
        
        if output_format == "txt":
            return self._assemble_txt(text_source, translations, file_name)
        elif output_format == "json":
            return self._assemble_json(text_source, translations, file_name)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _assemble_txt(self, 
                    text_source: TextSource, 
                    translations: Dict[int, str],
                    file_name: str) -> str:
        """
        Assemble translations into a plain text file.
        
        Args:
            text_source: The source text being translated
            translations: Dictionary mapping sentence indices to translations
            file_name: Base name for the output file
            
        Returns:
            Path to the generated translation file
        """
        output_path = os.path.join(self.output_dir, f"{file_name}.txt")
        
        with open(output_path, 'w', encoding='utf-8') as file:
            for i, sentence in enumerate(text_source.sentences):
                if i in translations:
                    file.write(f"{translations[i]}")
                    # Add space or newline based on the original text structure
                    if sentence.endswith('.') or sentence.endswith('!') or sentence.endswith('?'):
                        file.write('\n')
                    else:
                        file.write(' ')
                else:
                    # Mark untranslated sentences
                    file.write(f"[UNTRANSLATED: {sentence}]")
        
        return output_path
    
    def _assemble_json(self, 
                     text_source: TextSource, 
                     translations: Dict[int, str],
                     file_name: str) -> str:
        """
        Assemble translations into a JSON file with both original and translated text.
        
        Args:
            text_source: The source text being translated
            translations: Dictionary mapping sentence indices to translations
            file_name: Base name for the output file
            
        Returns:
            Path to the generated translation file
        """
        output_path = os.path.join(self.output_dir, f"{file_name}.json")
        
        # Create data structure
        data = {
            "title": text_source.title,
            "author": text_source.author,
            "source_language": text_source.language,
            "target_language": text_source.target_language,
            "sentences": []
        }
        
        # Add sentences
        for i, original in enumerate(text_source.sentences):
            sentence_data = {
                "index": i,
                "original": original,
                "translation": translations.get(i, "[UNTRANSLATED]")
            }
            data["sentences"].append(sentence_data)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        
        return output_path
    
    def get_translation_status(self, 
                             text_source: TextSource, 
                             translations: Dict[int, str]) -> Dict:
        """
        Get statistics about the translation status.
        
        Args:
            text_source: The source text being translated
            translations: Dictionary mapping sentence indices to translations
            
        Returns:
            Dictionary with translation statistics
        """
        total_sentences = len(text_source.sentences)
        translated_sentences = len(translations)
        
        return {
            "title": text_source.title,
            "total_sentences": total_sentences,
            "translated_sentences": translated_sentences,
            "completion_percentage": (translated_sentences / total_sentences) * 100 if total_sentences > 0 else 0,
            "remaining_sentences": total_sentences - translated_sentences
        }
