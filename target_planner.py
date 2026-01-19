"""
Target genotype planner for Drosophila crosses (ROLE-BASED)

Sex is a BREEDING ROLE, not inherited.
- Female role ("F"): allowed only if genotype is "female-eligible"
- Male role ("M"): always allowed
Offspring are genotypes only (no sex field).

This file NOW validates:
- input stocks (when planning starts)
- target genotype (optional but recommended)
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from drosophila_cross_generator import InternalGenotype, AUTOSOME_CHROMOSOMES
from genotype_parser import external_to_internal
from cross_logic import (
    get_unique_offspring,
    is_lethal,
    has_balancer,
    validate_stock_genotype,
)


# ----------------------------------------------------------------------------
# Female eligibility (your biological constraint)
# ----------------------------------------------------------------------------

def is_homozygous(a1: str, a2: str) -> bool:
    return a1 == a2


def allowed_as_female_parent(genotype: InternalGenotype) -> bool:
    """
    Female role allowed if on every autosome:
    - homozygous: OK
    - heterozygous: at least one allele has a balancer marker
    """
    for chrom in AUTOSOME_CHROMOSOMES:
        if chrom not in genotype:
            continue
        a1, a2 = genotype[chrom]
        if is_homozygous(a1, a2):
            continue
        if not (has_balancer(a1) or has_balancer(a2)):
            return False
    return True


# ----------------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------------

@dataclass
class CrossPlan:
    generation: int
    parent1_name: str
    parent1_genotype: InternalGenotype
    parent1_sex: str  # "F" role
    parent2_name: str
    parent2_genotype: InternalGenotype
    parent2_sex: str  # "M" role
    target_genotype: InternalGenotype
    target_probability: float
    intermediate_genotype: Optional[InternalGenotype] = None
    intermediate_name: Optional[str] = None


@dataclass
class StockState:
    stock_name: str
    genotype: InternalGenotype
    role: str  # "F" or "M" (label only; actual role assignment is decided per cross)
    route_probability: float = 1.0
    provenance: List[CrossPlan] = field(default_factory=list)


@dataclass
class Brood:
    brood_id: str
    generation: int
    parent_f: StockState
    parent_m: StockState
    route_probability: float
    provenance_base: List[CrossPlan]
    offspring_distribution: List[Tuple[InternalGenotype, float]] = field(default_factory=list)


@dataclass
class BreedingPlan:
    steps: List[CrossPlan]
    total_generations: int
    target_probability: float
    target_genotype: InternalGenotype


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------

def genotypes_match(g1: InternalGenotype, g2: InternalGenotype) -> bool:
    if set(g1.keys()) != set(g2.keys()):
        return False
    for chrom in g1:
        if set(g1[chrom]) != set(g2[chrom]):
            return False
    return True


def merge_provenance(a: List[CrossPlan], b: List[CrossPlan]) -> List[CrossPlan]:
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return a + b[i:]


def iter_role_oriented_pairs(s1: StockState, s2: StockState) -> List[Tuple[StockState, StockState]]:
    """
    Return all valid (female_state, male_state) role assignments for crossing.
    """
    pairs: List[Tuple[StockState, StockState]] = []
    if allowed_as_female_parent(s1.genotype):
        pairs.append((s1, s2))
    if (s1 is not s2) and allowed_as_female_parent(s2.genotype):
        pairs.append((s2, s1))
    return pairs


# ----------------------------------------------------------------------------
# Sibling crosses (two virtuals from same brood)
# ----------------------------------------------------------------------------

def consider_sibling_crosses(
    brood: Brood,
    target_genotype: InternalGenotype,
    generation: int,
    max_generations: int,
    top_k_per_role: int = 20
) -> List[BreedingPlan]:
    plans: List[BreedingPlan] = []

    female_candidates: List[Tuple[int, InternalGenotype, float]] = []
    male_candidates: List[Tuple[int, InternalGenotype, float]] = []

    for idx, (g, f) in enumerate(brood.offspring_distribution):
        if is_lethal(g):
            continue
        male_candidates.append((idx, g, f))
        if allowed_as_female_parent(g):
            female_candidates.append((idx, g, f))

    female_candidates = female_candidates[:top_k_per_role]
    male_candidates = male_candidates[:top_k_per_role]

    for f_idx, f_gen, f_freq in female_candidates:
        for m_idx, m_gen, m_freq in male_candidates:
            if f_idx == m_idx:
                continue

            offspring2 = get_unique_offspring(f_gen, m_gen)
            if not offspring2:
                continue

            for child_gen, child_freq in offspring2:
                if genotypes_match(child_gen, target_genotype):
                    total_prob = brood.route_probability * f_freq * m_freq * child_freq

                    f_pick = CrossPlan(
                        generation=brood.generation,
                        parent1_name=brood.parent_f.stock_name,
                        parent1_genotype=brood.parent_f.genotype,
                        parent1_sex="F",
                        parent2_name=brood.parent_m.stock_name,
                        parent2_genotype=brood.parent_m.genotype,
                        parent2_sex="M",
                        target_genotype=f_gen,
                        target_probability=f_freq,
                        intermediate_genotype=f_gen,
                        intermediate_name=f"F{brood.generation}_{brood.brood_id}_sibF_{f_idx}",
                    )

                    m_pick = CrossPlan(
                        generation=brood.generation,
                        parent1_name=brood.parent_f.stock_name,
                        parent1_genotype=brood.parent_f.genotype,
                        parent1_sex="F",
                        parent2_name=brood.parent_m.stock_name,
                        parent2_genotype=brood.parent_m.genotype,
                        parent2_sex="M",
                        target_genotype=m_gen,
                        target_probability=m_freq,
                        intermediate_genotype=m_gen,
                        intermediate_name=f"F{brood.generation}_{brood.brood_id}_sibM_{m_idx}",
                    )

                    final = CrossPlan(
                        generation=generation,
                        parent1_name=f_pick.intermediate_name,
                        parent1_genotype=f_gen,
                        parent1_sex="F",
                        parent2_name=m_pick.intermediate_name,
                        parent2_genotype=m_gen,
                        parent2_sex="M",
                        target_genotype=target_genotype,
                        target_probability=child_freq,
                    )

                    steps = brood.provenance_base + [f_pick, m_pick, final]
                    plans.append(
                        BreedingPlan(
                            steps=steps,
                            total_generations=generation,
                            target_probability=total_prob,
                            target_genotype=target_genotype,
                        )
                    )

                    break  # found target for this sibling pair

    return plans


# ----------------------------------------------------------------------------
# Main planner
# ----------------------------------------------------------------------------

def plan_to_target(lab_stocks: List[Dict], target_genotype_str: str, max_generations: int) -> Optional[BreedingPlan]:
    target_genotype, _ = external_to_internal(target_genotype_str)

    # Validate target + input stocks here (ENFORCED even without GUI)
    validate_stock_genotype(target_genotype, context="target genotype")
    for s in lab_stocks:
        validate_stock_genotype(s["internal_genotype"], context=f"input stock '{s['name']}'")

    # initial states
    initial_states: List[StockState] = [
        StockState(stock_name=s["name"], genotype=s["internal_genotype"], role="M", route_probability=1.0, provenance=[])
        for s in lab_stocks
    ]

    states_by_gen: Dict[int, List[StockState]] = {0: initial_states}
    broods_by_gen: Dict[int, List[Brood]] = {}

    best: Optional[BreedingPlan] = None
    brood_counter = 0

    for generation in range(1, max_generations + 1):
        current_states = states_by_gen[0] + states_by_gen.get(generation - 1, [])
        next_states: List[StockState] = []
        gen_plans: List[BreedingPlan] = []

        # ---- standard crosses ----
        for i, s1 in enumerate(current_states):
            for s2 in current_states[i:]:
                if set(s1.genotype.keys()) != set(s2.genotype.keys()):
                    continue

                for fem_state, mal_state in iter_role_oriented_pairs(s1, s2):
                    dist = get_unique_offspring(fem_state.genotype, mal_state.genotype)
                    if not dist:
                        continue

                    brood_id = f"brood_{brood_counter}"
                    brood_counter += 1

                    brood = Brood(
                        brood_id=brood_id,
                        generation=generation,
                        parent_f=fem_state,
                        parent_m=mal_state,
                        route_probability=fem_state.route_probability * mal_state.route_probability,
                        provenance_base=merge_provenance(fem_state.provenance, mal_state.provenance),
                        offspring_distribution=dist,
                    )
                    broods_by_gen.setdefault(generation, []).append(brood)

                    # Check for target
                    for child_gen, child_freq in dist:
                        if genotypes_match(child_gen, target_genotype):
                            total_prob = brood.route_probability * child_freq

                            final = CrossPlan(
                                generation=generation,
                                parent1_name=fem_state.stock_name,
                                parent1_genotype=fem_state.genotype,
                                parent1_sex="F",
                                parent2_name=mal_state.stock_name,
                                parent2_genotype=mal_state.genotype,
                                parent2_sex="M",
                                target_genotype=target_genotype,
                                target_probability=child_freq,
                            )

                            steps = brood.provenance_base + [final]
                            gen_plans.append(
                                BreedingPlan(
                                    steps=steps,
                                    total_generations=generation,
                                    target_probability=total_prob,
                                    target_genotype=target_genotype,
                                )
                            )
                            break

                    # Create virtuals for next generation
                    if generation < max_generations:
                        top_k = min(20, len(dist))
                        for j, (child_gen, child_freq) in enumerate(dist[:top_k]):
                            if is_lethal(child_gen):
                                continue

                            child_route = brood.route_probability * child_freq

                            m_step = CrossPlan(
                                generation=generation,
                                parent1_name=fem_state.stock_name,
                                parent1_genotype=fem_state.genotype,
                                parent1_sex="F",
                                parent2_name=mal_state.stock_name,
                                parent2_genotype=mal_state.genotype,
                                parent2_sex="M",
                                target_genotype=child_gen,
                                target_probability=child_freq,
                                intermediate_genotype=child_gen,
                                intermediate_name=f"F{generation}_{fem_state.stock_name}_x_{mal_state.stock_name}_M_{j}",
                            )
                            m_prov = brood.provenance_base + [m_step]
                            next_states.append(
                                StockState(
                                    stock_name=m_step.intermediate_name,
                                    genotype=child_gen,
                                    role="M",
                                    route_probability=child_route,
                                    provenance=m_prov,
                                )
                            )

                            if allowed_as_female_parent(child_gen):
                                f_step = CrossPlan(
                                    generation=generation,
                                    parent1_name=fem_state.stock_name,
                                    parent1_genotype=fem_state.genotype,
                                    parent1_sex="F",
                                    parent2_name=mal_state.stock_name,
                                    parent2_genotype=mal_state.genotype,
                                    parent2_sex="M",
                                    target_genotype=child_gen,
                                    target_probability=child_freq,
                                    intermediate_genotype=child_gen,
                                    intermediate_name=f"F{generation}_{fem_state.stock_name}_x_{mal_state.stock_name}_F_{j}",
                                )
                                f_prov = brood.provenance_base + [f_step]
                                next_states.append(
                                    StockState(
                                        stock_name=f_step.intermediate_name,
                                        genotype=child_gen,
                                        role="F",
                                        route_probability=child_route,
                                        provenance=f_prov,
                                    )
                                )

        # ---- sibling crosses ----
        if generation > 1 and (generation - 1) in broods_by_gen:
            for brood in broods_by_gen[generation - 1]:
                gen_plans.extend(
                    consider_sibling_crosses(brood, target_genotype, generation, max_generations)
                )

        # prune virtuals/broods
        next_states.sort(key=lambda s: s.route_probability, reverse=True)
        states_by_gen[generation] = next_states[:30]

        if generation in broods_by_gen:
            broods_by_gen[generation].sort(key=lambda b: b.route_probability, reverse=True)
            broods_by_gen[generation] = broods_by_gen[generation][:50]

        # update best
        for p in gen_plans:
            if best is None:
                best = p
            else:
                if (p.total_generations < best.total_generations) or (
                    p.total_generations == best.total_generations and p.target_probability > best.target_probability
                ):
                    best = p

    return best
