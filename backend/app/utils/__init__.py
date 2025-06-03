"""
Utility functions package
"""
from .content_processing import extract_markdown_content
from .prompt_generation import generate_travel_prompt

__all__ = [
    "extract_markdown_content",
    "generate_travel_prompt"
]