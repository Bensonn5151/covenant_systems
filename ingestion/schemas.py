"""
Pydantic schemas for Bronze/Silver/Gold data layers.
These are the data contracts for Covenant Systems.

Run validation with: python3 validate_data.py
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


# =============================================================================
# BRONZE LAYER - Raw extraction metadata
# =============================================================================
class BronzeMetadata(BaseModel):
    """Metadata for raw extracted documents stored in storage/bronze/"""
    document_id: str = Field(..., min_length=1)
    source_file: str
    file_size_bytes: int = Field(..., gt=0)
    file_hash: str = Field(..., min_length=64, max_length=64)  # SHA256
    page_count: Optional[int] = Field(None, ge=0)
    char_count: int = Field(..., ge=0)
    extraction_date: datetime
    extraction_method: str
    fallback_reason: Optional[str] = None  # Present when Adobe fails and PyPDF2 used


# =============================================================================
# SILVER LAYER - Structured sections
# =============================================================================
class SectionMetadata(BaseModel):
    """Metadata attached to each Silver section"""
    document_id: str
    document_type: str  # Act, Regulation, Guidance
    jurisdiction: str   # federal, provincial, etc.
    source_file: str
    processed_date: datetime
    category: str       # act, regulation, guidance
    is_toc: bool = False

    class Config:
        extra = "allow"  # Allow additional fields


class SilverSection(BaseModel):
    """A single parsed section from Silver layer (storage/silver/)"""
    section_id: str = Field(..., min_length=1)
    section_number: str
    section_type: str
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    level: int = Field(..., ge=0)
    parent_id: Optional[str] = None
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., ge=0)
    metadata: SectionMetadata
    citations: List[str] = []

    @field_validator('end_char')
    @classmethod
    def end_after_start(cls, v, info):
        if 'start_char' in info.data and v < info.data['start_char']:
            raise ValueError('end_char must be >= start_char')
        return v

    @field_validator('title')
    @classmethod
    def title_has_document_prefix(cls, v):
        """Ensure title contains document prefix (e.g., 'Bank Act > Section 1')"""
        if ' > ' not in v:
            raise ValueError(f"Title missing document prefix ' > ': {v[:50]}...")
        return v


# =============================================================================
# GOLD LAYER - Embeddings
# =============================================================================
class GoldMetadata(BaseModel):
    """Metadata for Gold layer embeddings (storage/gold/*/metadata.json)"""
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    count: int = Field(..., ge=0)
    normalized: bool = True


class GoldSection(BaseModel):
    """Silver section with embedding attached (storage/gold/*/sections.json)"""
    section_id: str = Field(..., min_length=1)
    section_number: str
    section_type: str
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    level: int = Field(..., ge=0)
    parent_id: Optional[str] = None
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., ge=0)
    metadata: SectionMetadata
    citations: List[str] = []
    embedding: List[float] = Field(..., min_length=384, max_length=384)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    @field_validator('embedding')
    @classmethod
    def valid_embedding(cls, v):
        import math
        if any(math.isnan(x) or math.isinf(x) for x in v):
            raise ValueError('Embedding contains NaN or Inf values')
        return v

    @field_validator('title')
    @classmethod
    def title_has_document_prefix(cls, v):
        """Ensure title contains document prefix"""
        if ' > ' not in v:
            raise ValueError(f"Title missing document prefix ' > ': {v[:50]}...")
        return v
