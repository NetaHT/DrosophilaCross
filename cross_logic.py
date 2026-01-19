"""
Cross logic for generating offspring genotypes in Drosophila melanogaster (ROLE-BASED)

Key design:
- Offspring do NOT have sex. Offspring are genotypes only.
- "Sex" is a BREEDING ROLE:
  - Female role ("F"): recombination possible (we do not generate recombinants; course-scope simplification)
  - Male role ("M"): no recombination
- Viability (lethality) is filtered here.
- "Female-eligible" (balanced unless homozygous) is handled in target_planner.py.
- Stock validity checks (lethal / homozygous balancer) are centralized here.
"""

from typing import List, Tuple, Dict
from drosophila_cross_generator import InternalGenotype, Sex

# Lethality markers: genotype is lethal only if SAME marker appears in both alleles of same chromosome.
LETHALITY_MARKERS = {"Sp", "CyO", "TM6B", "TM3", "MKRS", "Pin"}

# Balancer markers (for suppressing recombination on autosomes in females)
# NOTE: include MKRS if you treat it as a balancer (many labs do).
BALANCER_MARKERS = {"FM7", "CyO", "TM6B", "TM3", "MKRS"}


# -----------------------------------------------------------------------------
# Viability and balancer helpers
# -----------------------------------------------------------------------------

def is_lethal(genotype: InternalGenotype) -> bool:
    for chrom, alleles in genotype.items():
        if not isinstance(alleles, tuple) or len(alleles) != 2:
            continue
        a1, a2 = alleles
        for marker in LETHALITY_MARKERS:
            if (marker in a1) and (marker in a2):
                return True
    return False


def has_balancer(allele: str) -> bool:
    return any(marker in allele for marker in BALANCER_MARKERS)


# -----------------------------------------------------------------------------
# NEW: Stock/genotype validation helpers (used by GUI + planner)
# -----------------------------------------------------------------------------

def has_homozygous_balancer(genotype: InternalGenotype) -> bool:
    """
    Returns True if any chromosome has the SAME balancer marker in both alleles.
    Examples:
      - 2:CyO/CyO   -> True
      - 3:TM3/TM3   -> True
      - 3:MKRS/MKRS -> True
      - 3:TM3/TM6B  -> False
    """
    for chrom, alleles in genotype.items():
        if not isinstance(alleles, tuple) or len(alleles) != 2:
            continue
        a1, a2 = alleles
        for marker in BALANCER_MARKERS:
            if (marker in a1) and (marker in a2):
                return True
    return False


def validate_stock_genotype(genotype: InternalGenotype, context: str = "genotype") -> None:
    """
    Raises ValueError if genotype is invalid as a stock/parent/target.

    Enforces:
    1) Lethality rule (same lethality marker on both alleles of a chromosome)
    2) Homozygous balancer forbidden (same balancer marker on both alleles)
    """
    if is_lethal(genotype):
        raise ValueError(
            f"Invalid {context}: genotype is lethal (same lethality marker on both alleles of a chromosome)."
        )

    if has_homozygous_balancer(genotype):
        raise ValueError(
            f"Invalid {context}: genotype has a homozygous balancer (same balancer on both alleles, e.g. CyO/CyO)."
        )


# -----------------------------------------------------------------------------
# Gametes and crossing (course-scope: independent assortment only)
# -----------------------------------------------------------------------------

def get_gametes(parent_genotype: InternalGenotype, role: Sex) -> List[Dict[str, str]]:
    """
    Return all possible gametes as dict[chrom] = allele.

    Course-scope simplification:
    - We do not model loci within chromosomes -> no recombinant haplotypes generated.
    - Role only changes recombination conceptually, but output set is the same here.
    """
    gametes: List[Dict[str, str]] = [{}]
    chromosome_order = sorted(parent_genotype.keys(), key=lambda c: (c != "X", c))

    for chrom in chromosome_order:
        allele1, allele2 = parent_genotype[chrom]
        new_gametes: List[Dict[str, str]] = []

        # For our simplified model, both roles output allele1 and allele2 if heterozygous.
        for g in gametes:
            g1 = dict(g)
            g1[chrom] = allele1
            new_gametes.append(g1)

            if allele2 != allele1:
                g2 = dict(g)
                g2[chrom] = allele2
                new_gametes.append(g2)

        gametes = new_gametes

    return gametes


def cross(parent_f_genotype: InternalGenotype, parent_m_genotype: InternalGenotype) -> List[InternalGenotype]:
    """
    Cross using explicit roles: female parent genotype × male parent genotype.
    Returns ALL viable offspring genotypes (with multiplicity).
    """
    if set(parent_f_genotype.keys()) != set(parent_m_genotype.keys()):
        raise ValueError("Parents must have the same chromosome set")

    f_gametes = get_gametes(parent_f_genotype, "F")
    m_gametes = get_gametes(parent_m_genotype, "M")

    offspring: List[InternalGenotype] = []
    for fg in f_gametes:
        for mg in m_gametes:
            child: InternalGenotype = {}
            for chrom in sorted(fg.keys()):
                child[chrom] = (fg[chrom], mg[chrom])

            if is_lethal(child):
                continue

            offspring.append(child)

    return offspring


def genotype_to_key(genotype: InternalGenotype) -> Tuple:
    return tuple((chrom, tuple(genotype[chrom])) for chrom in sorted(genotype.keys()))


def get_unique_offspring(parent_f_genotype: InternalGenotype,
                         parent_m_genotype: InternalGenotype) -> List[Tuple[InternalGenotype, float]]:
    """
    Returns [(genotype, frequency)] sorted by frequency desc.
    Frequency is count / total viable offspring (after lethality filtering).
    """
    all_offspring = cross(parent_f_genotype, parent_m_genotype)
    total = len(all_offspring)
    if total == 0:
        return []

    counts: Dict[Tuple, int] = {}
    for g in all_offspring:
        k = genotype_to_key(g)
        counts[k] = counts.get(k, 0) + 1

    out: List[Tuple[InternalGenotype, float]] = []
    for k, c in counts.items():
        genotype = {chrom: alleles for chrom, alleles in k}
        out.append((genotype, c / total))

    out.sort(key=lambda x: x[1], reverse=True)
    return out
