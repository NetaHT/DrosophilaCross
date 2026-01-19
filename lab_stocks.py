"""
Lab stocks data management for reading and accessing available lab stocks
"""

from typing import List, Dict, Tuple
import pandas as pd
from pathlib import Path
from genotype_parser import external_to_internal
from drosophila_cross_generator import InternalGenotype, Sex


def read_lab_stocks(file_path: str = "lab stocks.xlsx") -> List[Dict]:
    """
    Read lab stocks data from an Excel file.
    
    Supports two formats:
    
    Format 1 (Detailed):
    - Stock name/ID column (name, stock_name, id, stock_id, stock number)
    - Genotype column in external format (e.g., "X:w/w 2:CyO/+ 3:+/+ 4:+/+")
    - Sex column ("F" for female, "M" for male)
    - Notes column (optional)
    
    Format 2 (Chromosome-based):
    - Stock name/ID column (stock number, stock name)
    - Individual chromosome columns (chromosome x, chromosome 2, chromosome 3, chromosome 4)
    - Sex is inferred from chromosome data
    - Notes column (optional)
    
    Args:
        file_path: Path to the lab stocks Excel file. Defaults to "lab stocks.xlsx"
                   in the current directory.
    
    Returns:
        List of dictionaries, each containing:
        - 'name': Stock name/ID
        - 'genotype': External format genotype string
        - 'sex': Sex of the stock ("F" or "M")
        - 'internal_genotype': Parsed internal format genotype
        - 'notes': Additional notes (if present in file)
    
    Raises:
        FileNotFoundError: If the Excel file is not found
        ValueError: If required columns are missing or data is invalid
    """
    # Check if file exists
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Lab stocks file not found: {file_path}")
    
    # Read Excel file
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
    
    # Identify column names (case-insensitive)
    column_names_lower = {col.lower().strip(): col for col in df.columns}
    
    # Detect format by looking for chromosome columns
    has_chromosome_format = any(
        'chromosome' in col for col in column_names_lower.keys()
    )
    
    lab_stocks = []
    
    if has_chromosome_format:
        # Format 2: Chromosome-based format
        _parse_chromosome_format(df, column_names_lower, lab_stocks)
    else:
        # Format 1: Detailed genotype format
        _parse_genotype_format(df, column_names_lower, lab_stocks)
    
    if not lab_stocks:
        raise ValueError("No stocks found in the Excel file")
    
    return lab_stocks


def _parse_genotype_format(df: pd.DataFrame, column_names_lower: Dict, lab_stocks: List[Dict]):
    """Parse Excel file in genotype format (single genotype column)"""
    # Find columns
    col_mapping = {}
    
    # Find name column
    name_keywords = ['name', 'stock_name', 'id', 'stock_id', 'stock number']
    for keyword in name_keywords:
        for col_key in column_names_lower:
            if keyword in col_key:
                col_mapping['name'] = column_names_lower[col_key]
                break
        if 'name' in col_mapping:
            break
    
    # Find genotype column
    genotype_keywords = ['genotype', 'genotype_external', 'external_genotype']
    for keyword in genotype_keywords:
        for col_key in column_names_lower:
            if keyword in col_key:
                col_mapping['genotype'] = column_names_lower[col_key]
                break
        if 'genotype' in col_mapping:
            break
    
    # Find sex column
    for col_key in column_names_lower:
        if 'sex' in col_key:
            col_mapping['sex'] = column_names_lower[col_key]
            break
    
    # Validate
    if 'name' not in col_mapping or 'genotype' not in col_mapping:
        raise ValueError(
            f"Required columns not found. Available: {list(df.columns)}"
        )
    
    # Parse stocks
    for idx, row in df.iterrows():
        try:
            stock_name = str(row[col_mapping['name']]).strip()
            genotype_str = str(row[col_mapping['genotype']]).strip()
            
            internal_genotype, _ = external_to_internal(genotype_str)
            
            owner = str(row.get(col_mapping.get('owner', ''), '')).strip() if 'owner' in col_mapping else ""
            notes = str(row.get(col_mapping.get('notes', ''), '')).strip() if 'notes' in col_mapping else ""
            
            # Create single entry per stock (sex-agnostic)
            # Gender will be determined dynamically during crossing
            lab_stocks.append({
                'name': stock_name,
                'genotype': genotype_str,
                'internal_genotype': internal_genotype,
                'owner': owner,
                'notes': notes
            })
        except Exception as e:
            raise ValueError(f"Error processing row {idx + 2}: {e}")


def _parse_chromosome_format(df: pd.DataFrame, column_names_lower: Dict, lab_stocks: List[Dict]):
    """Parse Excel file in chromosome format (separate columns for each chromosome)"""
    # Find name column
    name_col = None
    name_keywords = ['stock number', 'stock_number', 'name', 'stock_name', 'id']
    for keyword in name_keywords:
        for col_key in column_names_lower:
            if keyword in col_key:
                name_col = column_names_lower[col_key]
                break
        if name_col:
            break
    
    if not name_col:
        raise ValueError(f"Stock name/ID column not found. Available: {list(df.columns)}")
    
    # Find owner column (optional)
    owner_col = None
    owner_keywords = ['stock owner', 'owner']
    for keyword in owner_keywords:
        for col_key in column_names_lower:
            if keyword in col_key:
                owner_col = column_names_lower[col_key]
                break
        if owner_col:
            break
    
    # Find notes column (optional)
    notes_col = None
    notes_keywords = ['notes', 'note']
    for keyword in notes_keywords:
        for col_key in column_names_lower:
            if keyword in col_key:
                notes_col = column_names_lower[col_key]
                break
        if notes_col:
            break
    
    # Find chromosome columns (only 2, 3, 4 - no X)
    chrom_cols = {}
    for col_key in column_names_lower:
        if 'chromosome' in col_key:
            # Extract chromosome name (2, 3, 4 only - no X)
            col_name = column_names_lower[col_key]
            if '2' in col_key:
                chrom_cols['2'] = col_name
            elif '3' in col_key:
                chrom_cols['3'] = col_name
            elif '4' in col_key:
                chrom_cols['4'] = col_name
            # Skip chromosome X
    
    # Parse stocks
    for idx, row in df.iterrows():
        try:
            stock_name = str(row[name_col]).strip()
            owner = str(row[owner_col]).strip() if owner_col else ""
            
            # Skip rows with no name
            if not stock_name or stock_name.lower() == 'nan':
                continue
            
            # Build genotype from chromosome data (only 2, 3, 4)
            genotype_parts = []
            has_valid_data = False
            
            for chrom in ['2', '3', '4']:
                if chrom in chrom_cols:
                    cell_value = row[chrom_cols[chrom]]
                    # Check for NaN or None
                    if pd.isna(cell_value) or str(cell_value).strip().lower() == 'nan':
                        alleles_str = ""
                    else:
                        alleles_str = str(cell_value).strip()
                        alleles_str = alleles_str.replace(' ', '')
                        has_valid_data = True
                    
                    if alleles_str:
                        genotype_parts.append(f"{chrom}:{alleles_str}")
            
            # Skip rows with no chromosome data
            if not has_valid_data:
                continue
            
            genotype_str = " ".join(genotype_parts)
            
            # Parse to validate and get internal format
            internal_genotype = {}
            
            for chrom_entry in genotype_str.split():
                if ':' not in chrom_entry:
                    continue
                    
                chrom, alleles_str = chrom_entry.split(':', 1)
                
                if '/' not in alleles_str:
                    # Single allele for autosome - convert to diploid
                    internal_genotype[chrom] = (alleles_str, alleles_str)
                else:
                    # Diploid - split by /
                    parts = alleles_str.split('/')
                    if len(parts) != 2:
                        raise ValueError(f"Invalid allele format: {alleles_str}")
                    allele1, allele2 = parts
                    internal_genotype[chrom] = (allele1, allele2)
            
            # Create single entry per stock (sex-agnostic)
            # Gender will be determined dynamically during crossing
            notes_str = str(row[notes_col]).strip() if notes_col and not pd.isna(row[notes_col]) else ""
            
            lab_stocks.append({
                'name': stock_name,
                'genotype': genotype_str,
                'owner': owner,
                'internal_genotype': internal_genotype,
                'notes': notes_str
            })
        except Exception as e:
            raise ValueError(f"Error processing row {idx + 2}: {e}")


def get_stock_by_name(lab_stocks: List[Dict], stock_name: str) -> Dict:
    """
    Retrieve a specific stock by name from the lab stocks list.
    
    Args:
        lab_stocks: List of lab stock dictionaries (from read_lab_stocks)
        stock_name: Name of the stock to retrieve
    
    Returns:
        Dictionary containing the stock data
        
    Raises:
        ValueError: If stock is not found
    """
    for stock in lab_stocks:
        if stock['name'].lower() == stock_name.lower():
            return stock
    
    available_names = [s['name'] for s in lab_stocks]
    raise ValueError(f"Stock '{stock_name}' not found. Available stocks: {available_names}")


def list_lab_stocks(lab_stocks: List[Dict]) -> None:
    """
    Display all available lab stocks in a formatted table.
    
    Args:
        lab_stocks: List of lab stock dictionaries (from read_lab_stocks)
    """
    print("\n=== Available Lab Stocks ===\n")
    print(f"{'Stock Name':<20} {'Sex':<5} {'Genotype':<40} {'Notes':<30}")
    print("-" * 100)
    for stock in lab_stocks:
        name = stock['name'][:20]
        sex = stock['sex']
        genotype = stock['genotype'][:40]
        notes = stock.get('notes', '')[:30]
        print(f"{name:<20} {sex:<5} {genotype:<40} {notes:<30}")
    print()


if __name__ == "__main__":
    # Example usage
    try:
        # Read lab stocks from Excel file
        stocks = read_lab_stocks()
        
        # Display all stocks
        list_lab_stocks(stocks)
        
        # Example: retrieve a specific stock
        print("\n=== Stock Details ===\n")
        if stocks:
            first_stock = stocks[0]
            print(f"Stock Name: {first_stock['name']}")
            print(f"Genotype: {first_stock['genotype']}")
            print(f"Sex: {first_stock['sex']}")
            print(f"Internal Genotype: {first_stock['internal_genotype']}")
            print(f"Notes: {first_stock.get('notes', 'N/A')}")
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
