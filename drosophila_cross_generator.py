"""
Base module for Drosophila cross generator
Defines core types and constants used throughout the project
"""

from typing import Dict, Tuple

# Type definitions
InternalGenotype = Dict[str, Tuple[str, str]]
"""
Internal genotype format: dictionary mapping chromosome to tuple of two alleles.
Example: {"X": ("w", "w"), "2": ("CyO", "+"), "3": ("TM6B", "+"), "4": ("+", "+")}
"""

Sex = str  # "F" for female, "M" for male
"""Sex type: either "F" for female or "M" for male"""

# Valid chromosomes in Drosophila melanogaster
VALID_CHROMOSOMES = {"2", "3", "4"}
"""Set of valid chromosome names for D. melanogaster (autosomes only, no sex chromosome)"""

AUTOSOME_CHROMOSOMES = {"2", "3", "4"}
"""Set of autosome chromosome names (non-sex chromosomes)"""

# Default genotype template
DEFAULT_GENOTYPE_TEMPLATE: InternalGenotype = {
    "2": ("+", "+"),
    "3": ("+", "+"),
    "4": ("+", "+"),
}
"""Template for a wild-type (normal) genotype"""

__version__ = "1.0.0"
__author__ = "Drosophila Genetics Lab"
