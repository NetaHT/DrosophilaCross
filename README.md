# Drosophila Cross Generator
A Python tool for designing crossing schemes to reach a desired target genotype in Drosophila melanogaster.

## 🧬 Biological Background
_Drosophila melanogaster _ is considered a primary genetic model due to its short generation time, well-characterized mutations, and easily scored phenotypes. Many genetic experiments rely on combining or maintaining specific alleles across generations, which is complicated by meiotic recombination. To manage this, researchers use **balancer chromosomes**—genetically engineered chromosomes containing large inversions that **suppress recombination**, a **dominant visible marker** (such as Curly wings), and typically a **recessive lethal element**. These properties allow balancers to preserve entire chromosome arms intact, prevent unwanted genetic shuffling, and make it straightforward to maintain lethal or unstable genotypes in stable laboratory stocks.\
Therefore, planning crossing schemes is a fundamental skill in _Drosophila_ labs to generate flies with the desired genetic profile, while optimizing labor and time. 

## ⭐ Project Overview
The program focuses on a useful real-world challenge:\
**Given a set of available fly stocks and a desired target genotype, what crosses can lead to that genotype?**
The planner simulates possible crosses, evaluates offspring genotypes, and suggests candidate crossing paths over 1–2 generations.

## 🎯 Key Features
1. Target genotype planning:
   - The user specifies: a list of available starting stock + a desired target genotype.
   - The program searches possible cross combinations to determine: whether the genotyope is reachable, what crosses could produce it, which parent genotypes need to be selected at each step.
2. Offspring Genotype Predictor (Used internally by the planner):
   - Generates gametes from each parent
   - Produces all possible offspring genotypes
   - Calculates expected frequencies
   - Handles autosomal and X-linked loci
   - Supports balancers and lethal combinations
  
## 📖 Project layout (draft):
```bash
drosophila-target-planner/
│
├── gui.py              # main GUI app
├── planner.py          # crossing scheme search logic
├── genetics.py         # genotypes, gametes, crosses
├── data/
│   ├── stocks.json     # saved stocks
│   └── rules.json      # phenotype & balancer rules
└── README.md
```

## GUI
- list of common fly stocks
- add stock option
- target genotype selection
- max. generations to search (or unlimited)
- output + crossing scheme display
