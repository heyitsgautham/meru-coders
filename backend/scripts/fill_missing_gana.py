#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fill missing Gana patterns in the ML dataset using the Chanda model.

The CSV has columns: Shloka, L/G, Gana, chanda
L/G uses: 'u' for laghu (short), '-' for guru (long)
Gana should be in Devanagari script (य, र, त, न, भ, ज, स, म)

This script processes rows where:
1. L/G pattern exists
2. Gana is missing (NaN) or numeric (invalid)
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import Chanda
from config import settings


def normalize_lg_pattern(lg_str: str) -> str:
    """
    Convert CSV L/G pattern to internal format.
    CSV uses: 'u' for laghu, '-' for guru
    Internal uses: 'L' for laghu, 'G' for guru
    """
    if pd.isna(lg_str):
        return None
    return lg_str.replace('u', 'L').replace('-', 'G')


def compute_gana_for_line(chanda_obj: Chanda, lg_line: str) -> str:
    """
    Compute Gana pattern for a single line of L/G pattern.
    Returns Gana in Devanagari script.
    """
    if not lg_line or pd.isna(lg_line):
        return ''
    
    # Normalize L/G pattern
    normalized = normalize_lg_pattern(lg_line.strip())
    if not normalized:
        return ''
    
    # Compute Gana
    gana = chanda_obj.lg_to_gana(normalized)
    
    # Convert to Devanagari
    gana_devanagari = gana.translate(chanda_obj.ttable_out)
    
    return gana_devanagari


def compute_gana_multiline(chanda_obj: Chanda, lg_pattern: str) -> str:
    """
    Compute Gana pattern for multi-line L/G patterns.
    Each line is separated by newline.
    Returns Gana patterns in Devanagari, one per line.
    """
    if pd.isna(lg_pattern):
        return ''
    
    lines = lg_pattern.strip().split('\n')
    gana_lines = []
    
    for line in lines:
        gana = compute_gana_for_line(chanda_obj, line)
        gana_lines.append(gana)
    
    return '\n'.join(gana_lines)


def is_valid_gana(gana_val) -> bool:
    """
    Check if Gana value is valid (not NaN and not numeric).
    """
    if pd.isna(gana_val):
        return False
    gana_str = str(gana_val).strip()
    # If it's purely numeric, it's invalid
    if gana_str.replace('.', '').isdigit():
        return False
    # If it's empty, it's invalid
    if not gana_str:
        return False
    return True


def fill_missing_gana(input_csv: str, output_csv: str = None, verbose: bool = True):
    """
    Fill missing Gana patterns in the CSV dataset.
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file (default: overwrites input)
        verbose: Print progress information
    """
    # Initialize Chanda
    chanda = Chanda(data_path=str(settings.DATA_DIR))
    
    if verbose:
        print(f"Loading CSV: {input_csv}")
    
    # Read CSV (skip first row which has col1, col2, col3 headers)
    df = pd.read_csv(input_csv, skiprows=1)
    
    if verbose:
        print(f"Total rows: {len(df)}")
    
    # Count rows that need Gana filled
    needs_gana_mask = (
        df['L/G'].notna() & 
        df['Shloka'].notna() & 
        ~df['Gana'].apply(is_valid_gana)
    )
    needs_gana_count = needs_gana_mask.sum()
    
    if verbose:
        print(f"Rows needing Gana computation: {needs_gana_count}")
    
    if needs_gana_count == 0:
        print("No rows need Gana computation. Exiting.")
        return
    
    # Process rows
    filled_count = 0
    for idx in df[needs_gana_mask].index:
        lg_pattern = df.at[idx, 'L/G']
        
        # Compute Gana
        gana = compute_gana_multiline(chanda, lg_pattern)
        
        if gana:
            df.at[idx, 'Gana'] = gana
            filled_count += 1
            
            if verbose and filled_count % 1000 == 0:
                print(f"Processed {filled_count}/{needs_gana_count} rows...")
    
    if verbose:
        print(f"Filled {filled_count} Gana patterns")
    
    # Save to output
    if output_csv is None:
        output_csv = input_csv
    
    # Add back the original header row
    with open(output_csv, 'w', encoding='utf-8') as f:
        f.write('col1,col2,col3,chanda,Unnamed: 4\n')
        df.to_csv(f, index=False)
    
    if verbose:
        print(f"Saved to: {output_csv}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fill missing Gana patterns in ML dataset')
    parser.add_argument('--input', '-i', 
                        default='data/without gana rig - ML_base_dataset_COMPLETE_with_rigveda.csv',
                        help='Input CSV file path')
    parser.add_argument('--output', '-o', 
                        default=None,
                        help='Output CSV file path (default: overwrites input)')
    parser.add_argument('--quiet', '-q', 
                        action='store_true',
                        help='Suppress progress output')
    
    args = parser.parse_args()
    
    # Resolve paths relative to backend directory
    backend_dir = Path(__file__).parent.parent
    input_path = backend_dir / args.input
    output_path = backend_dir / args.output if args.output else None
    
    fill_missing_gana(
        str(input_path),
        str(output_path) if output_path else None,
        verbose=not args.quiet
    )


if __name__ == '__main__':
    main()
