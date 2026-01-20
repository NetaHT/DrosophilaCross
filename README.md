# Drosophila Breeding Planner

A comprehensive tool for planning optimal breeding strategies to achieve target genotypes in *Drosophila melanogaster*.

## Table of Contents
1. [Drosophila Background](#drosophila-background)
2. [What This Program Does](#what-this-program-does)
3. [Recombination & Genetics Rules](#recombination--genetics-rules)
4. [User Interface](#user-interface)
5. [Program Components](#program-components)
6. [Installation & Usage](#installation--usage)
7. [Genotype Format](#genotype-format)
8. [Advanced Features](#advanced-features)

---

## Drosophila Background

*Drosophila melanogaster* (fruit fly) is a model organism widely used in genetics research due to its:
- **Simple genome**: 4 chromosome pairs (3 autosomes + sex chromosomes)
- **Short lifecycle**: ~10 days from egg to adult
- **Well-characterized genetics**: Extensive stock libraries available
- **Balancer systems**: Special chromosomes that prevent recombination, essential for maintaining complex genotypes

### Key Concepts

**Balancer Chromosomes**: Specialized chromosomes carrying:
- Inversion(s) that suppress crossing-over (recombination)
- Recessive lethal alleles when homozygous

**Recombination**: Genetic exchange between homologous chromosomes during meiosis
- Occurs in **females** (heterozygous flies) → produces genetic variation in offspring
- Does **not** occur in **males** → offspring are always genetically identical to father for autosomes
- Suppressed by balancer inversions → allows stable maintenance of complex genotypes

Stable genetic lines (i.e. balanced or homozygous alleles) are reffered to as "stocks".

---

## What This Program Does

This planner solves a critical problem in fly genetics: **How do I breed flies to obtain a specific genotype?** This is a primary and essential aspect of fly genetics, which requires careful planning.

### Key Features
- ✅ **Automatic Planning**: Finds optimal crosses to reach target genotype
- ✅ **Multi-Generation Support**: Plans up to 5 generations ahead
- ✅ **Probability Calculation**: Computes likelihood of success for each plan
- ✅ **Lab Stock Management**: Maintains database of available stocks
- ✅ **GUI Interface**: User-friendly graphical application
- ✅ **Sibling Crossing**: Intelligently selects offspring from same brood for faster plans
- ✅ **Role-Based Sex Model**: Treats sex as a breeding role, not an inherited property

### Example Problem
**Goal**: Create flies with genotype `2:CyO/a 3:+/+ 4:+/+` from available stocks

**Solution**: The planner automatically:
1. Searches all pairwise crosses between available stocks
2. Tracks which offspring genotypes appear and their frequencies
3. Plans subsequent generations if needed
4. Returns the shortest plan with highest success probability

---

## Recombination & Genetics Rules

### Rule 1: Gender-Dependent Recombination

**FEMALES** (XX genotype):
- Undergo recombination during meiosis
- Produce varied offspring genotypes if heterozygous
- **Must be balanced** (have balancer on each heterozygous autosome) to maintain desired genotype in offspring
  - Balanced example: `2:CyO/a` ✓ (CyO balancer suppresses recombination)
  - Unbalanced example: `2:a/b` ✗ (recombination produces 2:a/b, 2:a/+, 2:b/+, etc.)

**MALES** (X/Y genotype):
- Do **not** undergo recombination
- Always produce offspring identical to themselves for autosomes
- Can have any genotype (no balance requirement)
- Females crossed with males always get paternal autosomes unchanged

### Rule 2: Homozygous Alleles Are Always Balanced

Any chromosome with identical alleles (homozygous) is considered  inherently balanced:
- `2:+/+` ✓ Wild-type, homozygous → no recombination possible
- `2:a/b` ✗ Heterozygous without balancer → recombination occurs

**Why?** If both alleles are identical, there's no genetic variation to segregate during meiosis.

### Rule 3: Lethality Rules

Certain allele combinations are lethal (non-viable offspring):
- Homozygous for same lethality marker: `CyO/CyO` ✗ (lethal)
- Lethality markers are not necessarily balancers. "Sp", "Pin" are lethal markers but not balancers, while "FM7" is the only balancer that is not lethal.

### Rule 4: Female × Male Crossing

- Crosses can **only** occur between one female and one male
- Same-sex crosses are biologically impossible and rejected
- The planner treats sex as a **breeding role**:
  - One parent acts as female (has recombination potential)
  - Another parent acts as male (no recombination)

---

## User Interface

### Starting the Program

```bash
python3 gui_planner.py
```

### Main Window - Three Tabs

#### Tab 1: Planner
Plan crosses to reach a target genotype.

**Inputs:**
1. **Parent Stocks**: At least one of the parents needs to suit a female genotype (balanced/homozygous alleles only), and the program will assign gender to the parents accrodingly.
Note: The program only supports autosomes.
   
3. **Target Genotype**: Enter desired genotype (format: `2:allele/allele 3:allele/allele 4:allele/allele`). "space" separates chromosomes, "/" separates alleles.
   
4. **Max Generations**: Search limit (1-5 generations)

**Output:**
- Displays complete breeding plan if found
- Shows:
  - Each generation and cross
  - Parent genotypes
  - Success probability (For each cross+overall)
  - Number of generations required
  - Note: Generation and cross are not the same, as two offspring from the same cross can be used as two parents for subsequent cross- The program will show a cross for each but this is in fact only one generation.

**Example:**
```
Generation 1: Cross 1
  Parent 1 (F): bottle (2:+/+ 3:+/+ 4:+/+)
  Parent 2 (M): bottle (2:+/+ 3:+/+ 4:+/+)
  Target Probability: 100.00%
```

#### Tab 2: Manage Stocks
View and edit the lab stock database.

**Features:**
- **View All Stocks**: Table showing all available flies
- **Search**: Find stocks by name, owner, genotype, sex, or notes
- **Add Stock**: Create new stock entry
  - Name (required)
  - Sex (F/M)
  - Genotype (format: `2:allele/allele 3:allele/allele 4:allele/allele`)
  - Notes (optional)

Changes are automatically saved to `lab stocks.xlsx`.

#### Tab 3: Results
Detailed display of the last breeding plan generated.

- Full plan with all steps
- Parent genotypes for each cross
- Intermediate selections (for sibling crosses)
- Target probability

---

## Program Components

### Core Genetics Module

**`drosophila_cross_generator.py`**
- Defines basic types and constants
- Chromosome definitions: `VALID_CHROMOSOMES = {"2", "3", "4"}`
- Autosome list: `AUTOSOME_CHROMOSOMES = {"2", "3", "4"}`
- Sex types: `"F"` (female) and `"M"` (male)
- Defines `InternalGenotype` format

### Genotype Parsing

**`genotype_parser.py`**
- Converts between **external format** (user-friendly) and **internal format** (computation)
- **External**: `"2:a/b 3:+/+ 4:+/+"` (what users see)
- **Internal**: `{"2": ("a", "b"), "3": ("+", "+"), "4": ("+", "+")}` (what code uses)
- Handles both formats from Excel and GUI input

### Genetics Logic

**`cross_logic.py`** - Heart of the genetics engine

Key functions:
- `has_balancer(allele)`: Checks if allele contains balancer (CyO, TM3, TM6B, FM7)
- `is_lethal(genotype)`: Checks if genotype is non-viable
- `is_balanced(genotype, sex)`: **Implements Rule 1 & 2**
  - For females: checks if balanced on all heterozygous autosomes
  - For males: always returns True (males don't recombine)
  - Homozygous chromosomes automatically pass (Rule 2)
- `get_gametes(genotype, sex)`: Produces gametes
  - Female gametes: can vary (recombination produces different allele combinations)
  - Male gametes: always parental type (no recombination)
- `cross(parent1, parent2)`: Creates offspring from two parents
  - Validates female × male requirement
  - Combines gametes
  - Filters for lethality and balance
- `get_unique_offspring()`: Returns unique genotypes with frequencies

### Lab Stock Management

**`lab_stocks.py`**
- Reads lab stock database from `lab stocks.xlsx`
- Supports two Excel formats:
  1. **Genotype-based**: Columns = Stock Name, Sex, Genotype, Notes
  2. **Chromosome-based**: Columns = Stock Number, Chromosome 2, 3, 4 (auto-converted)
- Returns list of stock dictionaries with internal genotypes
- Functions:
  - `read_lab_stocks()`: Load all stocks from Excel
  - Stock includes: name, sex, internal_genotype, owner, notes

### Breeding Plan Generation

**`target_planner.py`** - Advanced planning algorithm

Key features:
- **Role-Based Sex Model**: Treats sex as breeding role (not inherited from parents)
- **Virtual Stocks**: Tracks offspring as potential parents for next generation
  - Male-role states: created for all offspring (always allowed)
  - Female-role states: created only if `allowed_as_female_parent()` passes
- **Sibling Crosses**: Can cross two different offspring from same brood
  - Useful for shortening plans
  - Probability correctly computed (brood route probability counted once)
- **Multi-Generation Planning**: Plans up to max_generations
- **Probability Tracking**: Maintains cumulative route probability through all generations
- **Ranking**: Best plan = fewest generations, then highest probability

Key classes:
- `Brood`: Represents single cross event + offspring distribution
- `StockState`: Represents stock with (genotype, role_sex, route_probability, provenance)
- `CrossPlan`: Single breeding step
- `BreedingPlan`: Complete breeding strategy

Key function:
- `allowed_as_female_parent(genotype)`: Implements female eligibility predicate
  - Returns True if genotype can act as female (balanced or homozygous on all autosomes)
  - Returns False if any heterozygous autosome lacks a balancer

### User Interface

**`gui_planner.py`** - Tkinter-based GUI
- **Stock selection**: Dropdown menus with search capability
- **Manual input**: Direct genotype entry with validation
- **Results display**: Shows breeding plans clearly with generation/cross numbering
- **Database management**: Add/search stocks
- **Error handling**: User-friendly error messages

### Testing

**`test_cross_generator.py`** - Comprehensive test suite
- 16 test suites covering all components
- Tests genotype parsing, balancer detection, lethality, gamete production, crosses, frequencies
- Validates new rules: homozygous balance, female × male requirement
- All tests pass ✓

---

## Installation & Usage

### Requirements
- Python 3.7+
- pandas, openpyxl (for Excel handling)

### Setup

```bash
# Install dependencies
pip install pandas openpyxl

# Verify installation
python3 -c "import tkinter; print('tkinter OK')"
```

### Running the Program

**GUI Application:**
```bash
python3 gui_planner.py
```
---

## Genotype Format

### External Format (User-Facing)

```
2:allele1/allele2 3:allele1/allele2 4:allele1/allele2
```

**Examples:**
- Wild-type: `2:+/+ 3:+/+ 4:+/+`
- Curly chromosome 2: `2:CyO/+ 3:+/+ 4:+/+`
- Balanced transgene on chromosome 3: `2:+/+ 3:UAS-GFP/TM6 4:+/+`

### Internal Format (Computation)

Dictionary with chromosome keys:
```python
{
  "2": ("CyO", "+"),
  "3": ("+", "+"),
  "4": ("+", "+")
}
```
**Balancer notation:**
- Can include multiple features: `TM3,Sb` (Tuberous, Stubble)
- Can pair different balancers: `CyO/TM3` (both are balancers)

---

## Advanced Features

### Role-Based Sex Model

Sex is **not inherited** from parents. Instead:
- First parent in a cross acts as **female role**: undergoes recombination (if heterozygous)
- Second parent acts as **male role**: no recombination
- Offspring are then assigned roles based on eligibility:
  - Can be **male role** if genotype is anything
  - Can be **female role** if genotype passes `allowed_as_female_parent()`

**Advantage**: Flexible planning without genetic sex constraints

### Sibling Crossing

If you have a brood with multiple offspring genotypes:
- Select one offspring to act as female (if eligible)
- Select different offspring to act as male
- Cross them to produce F2
- Shortens plans by utilizing genetic diversity within single brood

**Example:**
```
F0: Cross A × B
F1: Brood contains genotypes [G1, G2, G3, ...]
F1→F2: Select G1 (female) × G2 (male) → can reach target in F2
       Instead of F0 → F1 → F2 → F3 with single F1 selected
```

## Testing & Verification

Run test suite to verify installation:

```bash
python3 test_cross_generator.py
```

Expected output: `✓ ALL TESTS PASSED (16/16)`