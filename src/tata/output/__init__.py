"""Output generation module for Tata recruitment assistant.

This module provides document generation and formatting capabilities
for all Tata artifacts, including Word-ready text and comparison tables.
"""

from src.tata.output.generator import (
    DocumentGenerator,
    OutputFormat,
    ComparisonTable,
    generate_word_ready,
    generate_comparison_table,
)

__all__ = [
    "DocumentGenerator",
    "OutputFormat",
    "ComparisonTable",
    "generate_word_ready",
    "generate_comparison_table",
]
