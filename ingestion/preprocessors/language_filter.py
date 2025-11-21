"""
Language Preprocessing for Bilingual Documents

Uses statistical language detection (langdetect) to filter content by language.

Architecture:
  Extract → Language Detection → Filter → Segment

This is a dedicated preprocessing step that tags content with language metadata
BEFORE it reaches the segmenter. The segmenter stays focused on structure only.

Why this approach:
- ✅ Robust: Uses n-gram probability models (99% accurate)
- ✅ Auditable: Preserves language metadata for debugging
- ✅ Separation of concerns: Language != Structure
- ✅ Flexible: Can preserve multiple languages or filter to one
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("⚠️  langdetect not installed. Run: pip install langdetect")


@dataclass
class TextBlock:
    """Represents a block of text with metadata."""
    text: str
    start_char: int
    end_char: int
    detected_lang: Optional[str] = None
    lang_confidence: Optional[float] = None


class LanguagePreprocessor:
    """
    Detects and filters content by language using statistical models.

    Uses langdetect (Google's language-detection library) which:
    - Supports 55+ languages
    - Uses character n-gram models
    - 99%+ accuracy for text > 20 chars
    """

    def __init__(
        self,
        target_lang: str = 'en',
        min_text_length: int = 20,
        keep_ambiguous: bool = True,
    ):
        """
        Initialize language preprocessor.

        Args:
            target_lang: Target language code (e.g., 'en', 'fr')
            min_text_length: Minimum text length for reliable detection
            keep_ambiguous: Keep blocks where detection fails (short text, numbers)
        """
        if not LANGDETECT_AVAILABLE:
            raise ImportError(
                "langdetect is required. Install with: pip install langdetect"
            )

        self.target_lang = target_lang
        self.min_text_length = min_text_length
        self.keep_ambiguous = keep_ambiguous

        # Stats for reporting
        self.stats = {
            'total_blocks': 0,
            'kept_blocks': 0,
            'filtered_blocks': 0,
            'ambiguous_blocks': 0,
            'languages_detected': {},
        }

    def filter_text(
        self,
        text: str,
        chunk_by: str = 'sentence',
    ) -> Tuple[str, Dict]:
        """
        Filter text to target language.

        Args:
            text: Input text (potentially bilingual)
            chunk_by: How to chunk text for detection ('paragraph', 'sentence', 'fixed')

        Returns:
            Tuple of (filtered_text, metadata)
        """
        # Reset stats
        self.stats = {
            'total_blocks': 0,
            'kept_blocks': 0,
            'filtered_blocks': 0,
            'ambiguous_blocks': 0,
            'languages_detected': {},
        }

        # Split into chunks
        chunks = self._chunk_text(text, chunk_by)

        # Detect language for each chunk
        filtered_chunks = []

        for chunk in chunks:
            self.stats['total_blocks'] += 1

            # Skip empty/very short chunks
            if len(chunk.text.strip()) < self.min_text_length:
                if self.keep_ambiguous:
                    filtered_chunks.append(chunk)
                    self.stats['ambiguous_blocks'] += 1
                continue

            # Detect language
            try:
                detected_lang = detect(chunk.text)
                chunk.detected_lang = detected_lang

                # Track language distribution
                self.stats['languages_detected'][detected_lang] = \
                    self.stats['languages_detected'].get(detected_lang, 0) + 1

                # Filter by target language
                if detected_lang == self.target_lang:
                    filtered_chunks.append(chunk)
                    self.stats['kept_blocks'] += 1
                else:
                    self.stats['filtered_blocks'] += 1
                    # Log dropped content for audit trail
                    preview = chunk.text[:50].replace('\n', ' ')
                    print(f"  [Dropped {detected_lang}]: {preview}...")

            except LangDetectException:
                # Detection failed (too short, numbers only, etc.)
                if self.keep_ambiguous:
                    filtered_chunks.append(chunk)
                    self.stats['ambiguous_blocks'] += 1

        # Reconstruct text from kept chunks
        filtered_text = '\n\n'.join(chunk.text for chunk in filtered_chunks)

        # Prepare metadata
        metadata = {
            'language_filter': {
                'target_lang': self.target_lang,
                'stats': self.stats.copy(),
            }
        }

        return filtered_text, metadata

    def _chunk_text(
        self,
        text: str,
        chunk_by: str,
    ) -> List[TextBlock]:
        """
        Split text into chunks for language detection.

        Args:
            text: Input text
            chunk_by: Chunking strategy

        Returns:
            List of TextBlock objects
        """
        if chunk_by == 'paragraph':
            return self._chunk_by_paragraph(text)
        elif chunk_by == 'sentence':
            return self._chunk_by_sentence(text)
        elif chunk_by == 'fixed':
            return self._chunk_by_fixed_size(text, size=500)
        else:
            raise ValueError(f"Unknown chunk_by: {chunk_by}")

    def _chunk_by_paragraph(self, text: str) -> List[TextBlock]:
        """Split by double newlines (paragraphs)."""
        chunks = []
        paragraphs = re.split(r'\n\s*\n', text)

        char_pos = 0
        for para in paragraphs:
            if para.strip():
                chunks.append(TextBlock(
                    text=para,
                    start_char=char_pos,
                    end_char=char_pos + len(para),
                ))
            char_pos += len(para) + 2  # +2 for \n\n

        return chunks

    def _chunk_by_sentence(self, text: str) -> List[TextBlock]:
        """Split by sentence boundaries."""
        # Simple sentence splitter (can be improved with NLTK)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        char_pos = 0
        for sent in sentences:
            if sent.strip():
                chunks.append(TextBlock(
                    text=sent,
                    start_char=char_pos,
                    end_char=char_pos + len(sent),
                ))
            char_pos += len(sent) + 1  # +1 for space

        return chunks

    def _chunk_by_fixed_size(
        self,
        text: str,
        size: int = 500,
    ) -> List[TextBlock]:
        """Split by fixed character size (with word boundaries)."""
        chunks = []
        char_pos = 0

        while char_pos < len(text):
            end_pos = min(char_pos + size, len(text))

            # Find word boundary
            if end_pos < len(text):
                # Look for space after current position
                space_pos = text.find(' ', end_pos)
                if space_pos > 0 and space_pos < end_pos + 50:
                    end_pos = space_pos

            chunk_text = text[char_pos:end_pos]

            if chunk_text.strip():
                chunks.append(TextBlock(
                    text=chunk_text,
                    start_char=char_pos,
                    end_char=end_pos,
                ))

            char_pos = end_pos + 1

        return chunks

    def print_stats(self):
        """Print filtering statistics."""
        print(f"\n{'='*60}")
        print("LANGUAGE FILTERING STATS")
        print(f"{'='*60}")
        print(f"Total blocks: {self.stats['total_blocks']}")
        print(f"Kept ({self.target_lang}): {self.stats['kept_blocks']}")
        print(f"Filtered: {self.stats['filtered_blocks']}")
        print(f"Ambiguous: {self.stats['ambiguous_blocks']}")
        print(f"\nLanguages detected:")
        for lang, count in sorted(
            self.stats['languages_detected'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {lang}: {count} blocks")
        print(f"{'='*60}\n")


# Convenience function
def filter_to_english(text: str) -> Tuple[str, Dict]:
    """
    Quick filter to English only.

    Args:
        text: Input text (potentially bilingual)

    Returns:
        Tuple of (english_only_text, metadata)
    """
    preprocessor = LanguagePreprocessor(target_lang='en')
    filtered_text, metadata = preprocessor.filter_text(text)
    preprocessor.print_stats()
    return filtered_text, metadata