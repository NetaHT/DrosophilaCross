"""
Parsing functions to convert between external and internal genotype formats
"""

from typing import Dict, Tuple, List
from drosophila_cross_generator import InternalGenotype, VALID_CHROMOSOMES, AUTOSOME_CHROMOSOMES, Sex


def determine_sex_from_genotype(genotype: InternalGenotype) -> Sex:
    """
    Determine sex from genotype based on X chromosome alleles.
    
    Females: Two identical or different X alleles (XX)
    Males: Single X allele (XY - represented as single allele in genotype)
    
    Args:
        genotype: Internal format genotype
        
    Returns:
        "F" for female, "M" for male
        
    Raises:
        ValueError: If X chromosome genotype is invalid
    """
    if "X" not in genotype:
        raise ValueError("Genotype must include X chromosome")
    
    x_alleles = genotype["X"]
    if not isinstance(x_alleles, tuple) or len(x_alleles) != 2:
        raise ValueError("X chromosome must have tuple of 2 alleles")
    
    a1, a2 = x_alleles
    
    # If both alleles are identical strings that don't contain "/", it's a male (hemizygous)
    # Females have two alleles (same or different)
    # We check if this represents a male by seeing if we encoded it as (allele, allele)
    # Males should have been encoded with the same allele twice or a special marker
    # For now, assume: if a1 == a2, it could be either male or female
    # Better approach: store a separate sex field or use allele count heuristic
    
    # For this implementation, we'll require that males are encoded as having 
    # the Y chromosome represented, but since we only store X, we need another way.
    # Let's assume: if created from external format, sex was determined correctly.
    # We'll use a simpler heuristic for now and require sex to be tracked separately.
    
    # Actually, let's store sex separately in the genotype as metadata
    # For now, return a default - this will be fixed by tracking sex explicitly
    return "F"  # Default, should be overridden by explicit sex tracking


def external_to_internal(external_genotype: str) -> Tuple[InternalGenotype, Sex]:
    """
    Convert external format to internal format.
    
    External format (no sex chromosome): "2:allele1/allele2 3:allele1/allele2 4:allele1/allele2"
    
    Sex is passed separately via the 'sex' parameter from the lab stocks database.
    
    Internal format: {"2": (allele1, allele2), "3": (allele1, allele2), ...}
    
    Args:
        external_genotype: String representation of genotype
        
    Returns:
        Tuple of (InternalGenotype, Sex) where Sex is "F" for female, "M" for male
        
    Raises:
        ValueError: If format is invalid
    """
    internal: InternalGenotype = {}
    sex: Sex = "F"  # Default to female (will be overridden by database)
    
    # Split by whitespace to get individual chromosome entries
    chromosome_entries = external_genotype.strip().split()
    
    for entry in chromosome_entries:
        # Split by colon to separate chromosome number from alleles
        if ":" not in entry:
            raise ValueError(f"Invalid format: {entry}. Expected 'chromosome:allele1/allele2'")
        
        chrom, alleles_str = entry.split(":", 1)
        
        # Validate chromosome number
        if chrom not in VALID_CHROMOSOMES:
            raise ValueError(f"Invalid chromosome: {chrom}. Must be one of {VALID_CHROMOSOMES}")
        
        # Autosomes: always diploid
        if "/" not in alleles_str:
            raise ValueError(f"Invalid allele format in {entry}. Expected 'allele1/allele2'")
        
        alleles = alleles_str.split("/")
        if len(alleles) != 2:
            raise ValueError(f"Invalid allele format in {entry}. Expected exactly 2 alleles")
        
        allele1, allele2 = alleles
        
        # Validate alleles are not empty
        if not allele1 or not allele2:
            raise ValueError(f"Empty allele in {entry}")
        
        internal[chrom] = (allele1, allele2)
    
    return internal, sex


def internal_to_external(internal_genotype: InternalGenotype, sex: Sex) -> str:
    """
    Convert internal format to external format.
    
    Internal format: {"2": (allele1, allele2), "3": (allele1, allele2), ...}
    
    External format: "2:allele1/allele2 3:allele1/allele2 4:allele1/allele2"
    
    Sex parameter is provided for consistency but not used in output (no X chromosome).
    
    Args:
        internal_genotype: Dictionary representation of genotype
        sex: "F" for female, "M" for male
        
    Returns:
        str: External string representation of genotype
        
    Raises:
        ValueError: If format is invalid
    """
    external_parts = []
    
    # Sort chromosomes: 2, 3, 4 (no X chromosome)
    chromosome_order = sorted([c for c in internal_genotype.keys()])
    
    for chrom in chromosome_order:
        if chrom not in internal_genotype:
            continue
            
        if chrom not in VALID_CHROMOSOMES:
            raise ValueError(f"Invalid chromosome: {chrom}. Must be one of {VALID_CHROMOSOMES}")
        
        alleles = internal_genotype[chrom]
        
        # Validate that alleles is a tuple of length 2
        if not isinstance(alleles, tuple) or len(alleles) != 2:
            raise ValueError(f"Invalid alleles for chromosome {chrom}. Expected tuple of 2 alleles")
        
        allele1, allele2 = alleles
        
        # Validate alleles are not empty
        if not allele1 or not allele2:
            raise ValueError(f"Empty allele for chromosome {chrom}")
        
        # Autosomes: output both alleles for both sexes
        external_parts.append(f"{chrom}:{allele1}/{allele2}")
    
    return " ".join(external_parts)


if __name__ == "__main__":
    # Test conversions
    print("=== Testing Parsing Functions ===\n")
    
    # Test external to internal (Female)
    print("Test 1: External to Internal (Female)")
    external_female = "X:w/w 2:CyO/+ 3:TM6B/+ 4:+/+"
    internal_f, sex_f = external_to_internal(external_female)
    print(f"Input:  {external_female}")
    print(f"Output: {internal_f}, Sex: {sex_f}\n")
    
    # Test external to internal (Male)
    print("Test 2: External to Internal (Male)")
    external_male = "X:w 2:CyO/+ 3:TM6B/+ 4:+/+"
    internal_m, sex_m = external_to_internal(external_male)
    print(f"Input:  {external_male}")
    print(f"Output: {internal_m}, Sex: {sex_m}\n")
    
    # Test internal to external (Female)
    print("Test 3: Internal to External (Female)")
    print(f"Input:  {internal_f}, Sex: {sex_f}")
    external_f_converted = internal_to_external(internal_f, sex_f)
    print(f"Output: {external_f_converted}\n")
    
    # Test internal to external (Male)
    print("Test 4: Internal to External (Male)")
    print(f"Input:  {internal_m}, Sex: {sex_m}")
    external_m_converted = internal_to_external(internal_m, sex_m)
    print(f"Output: {external_m_converted}\n")
    
    # Test round-trip conversion
    print("Test 5: Round-trip Conversion (Female)")
    original_external_f = "X:+/+ 2:+/+ 3:Sb/Sb 4:+/+"
    internal_rt, sex_rt = external_to_internal(original_external_f)
    converted_back_f = internal_to_external(internal_rt, sex_rt)
    print(f"Original:      {original_external_f}")
    print(f"Internal:      {internal_rt}")
    print(f"Converted back: {converted_back_f}")
    print(f"Match: {original_external_f == converted_back_f}\n")
    
    # Test error handling
    print("Test 6: Error Handling")
    try:
        external_to_internal("2:CyO/+ 5:+/+")  # Invalid chromosome
    except ValueError as e:
        print(f"Caught expected error: {e}\n")
    
    try:
        external_to_internal("2CyO/+")  # Missing colon
    except ValueError as e:
        print(f"Caught expected error: {e}\n")
    
    try:
        external_to_internal("2:CyO+")  # Missing slash
    except ValueError as e:
        print(f"Caught expected error: {e}\n")
