#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confusion Matrix Evaluation for Chandojñānam Model

This script evaluates the meter identification model against the
"page 1-47 chanda list - Sheet1.csv" dataset containing 100+ unique shlokas
with labeled chandas. It generates:
1. Overall accuracy metrics (Top-1 and Top-3)
2. Per-meter precision, recall, and F1 scores
3. Confusion matrix visualization
4. Detailed error analysis

@author: Chandojñānam Enhancement Project
@date: November 2025
"""

import sys
import os
import csv
import re
from pathlib import Path
from collections import Counter, defaultdict

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chanda import Chanda

# Optional visualization imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import numpy as np
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False

# Initialize Chanda
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data')
chanda = Chanda(DATA_PATH)

###############################################################################
# METER NAME NORMALIZATION
###############################################################################

# Map various spellings/transliterations to canonical names
# Format: {normalized_name: [list of variants]}
METER_SYNONYMS = {
    # Vedic/Common meters
    'anushtubh': ['anuṣṭup', 'anushtup', 'anushtubh', 'anustubh', 'anustup', 'अनुष्टुभ्', 'अनुष्टुप्', 'anuṣṭubh', 'अनुष्टुभ'],
    'trishtubh': ['triṣṭubh', 'trishtubh', 'त्रिष्टुभ्', 'त्रिष्टुभ', 'trishtup'],
    'jagati': ['jagatī', 'jagati', 'जगती', 'जगति'],
    'gayatri': ['gāyatrī', 'gayatri', 'gayatree', 'गायत्री'],
    'ushnik': ['uṣṇik', 'ushnik', 'उष्णिक्', 'उष्णिक'],
    'pankti': ['paṅkti', 'pankti', 'पङ्क्ति', 'पंक्ति'],
    'brihati': ['bṛhatī', 'brihati', 'बृहती'],
    
    # Classical meters - 11 syllable patterns (Trishtubh family)
    'indravajra': ['indravajrā', 'indravajra', 'इन्द्रवज्रा', 'इन्द्रवज्र'],
    'upendravajra': ['upendravajra', 'upendravajrā', 'उपेन्द्रवज्रा', 'उपेन्द्रवज्र'],
    'upajati': ['upajātiḥ', 'upajāti', 'upajati', 'उपजाति', 'उपजातिः'],
    'shalini': ['śālinī', 'shalini', 'salini', 'शालिनी'],
    'rathoddhata': ['rathoddhata', 'rathoddhātā', 'रथोद्धता', 'rathōddhata'],
    'svagata': ['svāgatā', 'svagata', 'स्वागता'],
    
    # Classical meters - 12 syllable patterns (Jagati family)
    'vamshastham': ['vaṁśasthavilam', 'vamshasthavila', 'vaṁśastha', 'vamshastham', 'वंशस्थ', 'वंशस्थविल', 'वंशशथविल'],
    'drutavilambita': ['drutavilambita', 'द्रुतविलम्बित', 'द्रुतविलंबित', 'druta-vilambita'],
    'totaka': ['toṭakam', 'totaka', 'toṭaka', 'तोटक', 'तोटकम्'],
    'bhujangaprayata': ['bhujangaprayātam', 'bhujangaprayāta', 'bhujangaprayata', 'भुजङ्गप्रयात', 'भुजंगप्रयात'],
    
    # Classical meters - 13+ syllable patterns
    'vasantatilaka': ['vasantatilakam', 'vasantatilaka', 'vasantatilakā', 'वसन्ततिलका', 'वसन्ततिलक'],
    'malini': ['mālinī', 'malini', 'mālini', 'मालिनी'],
    'praharsini': ['praharṣinī', 'praharsini', 'praharshini', 'प्रहर्षिणी'],
    
    # Classical meters - 17+ syllable patterns
    'mandakranta': ['mandäkräntä', 'mandākrāntā', 'mandakranta', 'mandākrānta', 'मन्दाक्रान्ता', 'मन्दाक्रान्त', 'मंदाक्रांता'],
    'shardula': ['śārdülavkrīḍita', 'śārdūlavikrīḍita', 'shardula', 'shardulavikridit', 'शार्दूलविक्रीडित', 'शार्दूलविक्रीडितम्', 'sārdulavikrīḍita'],
    'sragdhara': ['sragdharā', 'sragdhara', 'स्रग्धरा'],
    
    # Other meters
    'pancacamara': ['pañcacāmaram', 'pancacamara', 'pañcacāmara', 'पञ्चचामर', 'पंचचामर'],
    'tunaka': ['tūṇakam', 'tunaka', 'tūṇaka', 'तूणक', 'चामर'],
    'tvaritagati': ['tvaritagati', 'त्वरितगति'],
    'upacitra': ['upacitrā', 'upacitra', 'उपचित्रा'],
    'udgata': ['udgatā', 'udgata', 'उद्गता'],
    'gajagati': ['gajagati', 'गजगति'],
    
    # Meters that may be confused - special mapping
    'kalahansa': ['kalahaṁsa', 'kalahansa', 'कलहंस'],
    'apavaha': ['apavāha', 'apavaha', 'अपवाह'],
    'arnadandaka': ['arṇadaṇḍaka', 'arnadandaka', 'अर्णदण्डक'],
    'meghavispurjita': ['meghavispūrjita', 'meghavispurjita', 'मेघविस्फूर्जिता'],
    'atishayini': ['atiśāyinī', 'atishayini', 'अतिशायिनी'],
}

def normalize_meter_name(name):
    """
    Normalize meter name to a canonical form for comparison.
    Handles IAST, Devanagari, and various transliteration schemes.
    """
    if not name:
        return ''
    
    # Convert to lowercase for comparison
    name_lower = name.lower().strip()
    
    # Remove common suffixes/prefixes
    name_lower = re.sub(r'^(श्री|śrī)', '', name_lower)
    name_lower = re.sub(r'(छन्दस्|chandas)$', '', name_lower)
    
    # Check against synonyms
    for canonical, variants in METER_SYNONYMS.items():
        for variant in variants:
            if name_lower == variant.lower() or name.strip() == variant:
                return canonical
    
    # If no match found, return cleaned version
    return name_lower.replace(' ', '').replace('-', '').replace('_', '')


# Define meter families for lenient matching
# Trishtubh family: 11 syllables per pada (44 total for 4 padas)
TRISHTUBH_FAMILY = {'trishtubh', 'indravajra', 'upendravajra', 'upajati', 'shalini', 
                    'rathoddhata', 'svagata', 'dodhaka', 'shalinivishama'}

# Jagati family: 12 syllables per pada (48 total for 4 padas)
JAGATI_FAMILY = {'jagati', 'vamshastham', 'totaka', 'bhujangaprayata', 'drutavilambita',
                 'indravamsha', 'vamshasthavilam', 'praharshini'}


def is_family_match(expected_norm, predicted_norm):
    """
    Check if expected and predicted meters belong to the same family.
    Returns True for Trishtubh-family or Jagati-family matches.
    """
    # Trishtubh family match
    if expected_norm in TRISHTUBH_FAMILY and predicted_norm in TRISHTUBH_FAMILY:
        return True
    
    # Jagati family match  
    if expected_norm in JAGATI_FAMILY and predicted_norm in JAGATI_FAMILY:
        return True
    
    return False


def extract_top_meter(result, expected_meter=None):
    """
    Extract the top predicted meter from identification result.
    Returns (meter_name, confidence, match_rank) tuple.
    
    match_rank is:
    - 1 if expected meter is top-1
    - 2-3 if expected meter is in top-3
    - 0 if not found in top results
    """
    if not result or 'chanda' not in result:
        return None, 0.0, 0
    
    chanda_list = result.get('chanda', [])
    confidence_scores = result.get('confidence_scores', {})
    
    if not chanda_list:
        return None, 0.0, 0
    
    # Get top meter
    top_item = chanda_list[0]
    if isinstance(top_item, tuple):
        top_meter = top_item[0]
    else:
        top_meter = str(top_item)
    
    # Get confidence
    if confidence_scores and top_meter in confidence_scores:
        confidence = confidence_scores[top_meter][0]
    else:
        confidence = 0.0
    
    # Check match rank if expected_meter provided
    match_rank = 0
    if expected_meter:
        normalized_expected = normalize_meter_name(expected_meter)
        for idx, item in enumerate(chanda_list[:5]):  # Check top 5
            if isinstance(item, tuple):
                pred_name = item[0]
            else:
                pred_name = str(item)
            
            if normalize_meter_name(pred_name) == normalized_expected:
                match_rank = idx + 1
                break
    
    return top_meter, confidence, match_rank


###############################################################################
# DATA LOADING
###############################################################################

def load_test_data(csv_path):
    """
    Load test data from CSV file.
    Handles multi-line verses and filters out empty entries.
    
    Returns list of dicts: [{text, expected_chanda, lg_pattern, gana}, ...]
    """
    test_cases = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Skip header rows (first 2 rows are headers)
    data_rows = rows[2:]
    
    for row in data_rows:
        if len(row) < 4:
            continue
        
        shloka = row[0].strip() if row[0] else ''
        lg_pattern = row[1].strip() if len(row) > 1 and row[1] else ''
        gana = row[2].strip() if len(row) > 2 and row[2] else ''
        expected_chanda = row[3].strip() if len(row) > 3 and row[3] else ''
        
        # Skip if no text or no expected chanda
        if not shloka or not expected_chanda:
            continue
        
        # Clean up the shloka text
        # Remove verse markers and extra whitespace
        shloka = re.sub(r'\s+', ' ', shloka)
        shloka = shloka.strip('" ')
        
        test_cases.append({
            'text': shloka,
            'expected_chanda': expected_chanda,
            'lg_pattern': lg_pattern,
            'gana': gana
        })
    
    return test_cases


###############################################################################
# EVALUATION
###############################################################################

def evaluate_model(test_cases, verbose=False):
    """
    Run evaluation on all test cases.
    Returns detailed results and summary statistics.
    """
    results = []
    
    # Counters for metrics
    top1_correct = 0
    top3_correct = 0
    total = 0
    
    # Per-meter tracking
    true_positives = Counter()  # Correctly predicted
    false_positives = Counter()  # Predicted but wrong
    false_negatives = Counter()  # Should have predicted but didn't
    
    # Confusion matrix data
    confusion_data = []  # (expected, predicted) pairs
    
    print("=" * 80)
    print("CHANDOJÑĀNAM MODEL EVALUATION")
    print("=" * 80)
    print(f"Total test cases: {len(test_cases)}")
    print()
    
    for idx, case in enumerate(test_cases, 1):
        text = case['text']
        expected = case['expected_chanda']
        expected_norm = normalize_meter_name(expected)
        
        # Run identification
        try:
            # Check if multi-line verse (contains newlines or verse markers)
            is_multiline = '\n' in text or '।' in text or len(text) > 100
            
            if is_multiline:
                # Use identify_from_text for multi-line verses
                full_result = chanda.identify_from_text(text, verse=True, fuzzy=True)
                
                if full_result and full_result.get('result', {}).get('verse'):
                    verse_result = full_result['result']['verse'][0]
                    chanda_tuple = verse_result.get('chanda', ([], 0))
                    
                    if chanda_tuple and chanda_tuple[0]:
                        top_meter = chanda_tuple[0][0]  # First match name
                        confidence = chanda_tuple[1]  # Score
                        predicted = top_meter
                        predicted_norm = normalize_meter_name(predicted) if predicted else ''
                        
                        # Check match rank
                        match_rank = 0
                        for rank, meter_name in enumerate(chanda_tuple[0][:5], 1):
                            if normalize_meter_name(meter_name) == expected_norm:
                                match_rank = rank
                                break
                    else:
                        top_meter = None
                        confidence = 0.0
                        match_rank = 0
                        predicted = 'NOT_FOUND'
                        predicted_norm = 'not_found'
                else:
                    top_meter = None
                    confidence = 0.0
                    match_rank = 0
                    predicted = 'NOT_FOUND'
                    predicted_norm = 'not_found'
            else:
                # Use identify_line for single line
                result = chanda.identify_line(text, fuzzy=True)
                
                if result and result.get('found'):
                    top_meter, confidence, match_rank = extract_top_meter(result, expected)
                    predicted = top_meter
                    predicted_norm = normalize_meter_name(predicted) if predicted else ''
                else:
                    top_meter = None
                    confidence = 0.0
                    match_rank = 0
                    predicted = 'NOT_FOUND'
                    predicted_norm = 'not_found'
                
        except Exception as e:
            if verbose:
                print(f"Error processing verse {idx}: {e}")
                import traceback
                traceback.print_exc()
            predicted = 'ERROR'
            predicted_norm = 'error'
            confidence = 0.0
            match_rank = 0
            result = None
        
        # Record result
        is_top1_match = match_rank == 1
        is_top3_match = match_rank in [1, 2, 3]
        is_family_match_flag = is_family_match(expected_norm, predicted_norm)
        
        total += 1
        if is_top1_match:
            top1_correct += 1
            true_positives[expected_norm] += 1
        else:
            false_negatives[expected_norm] += 1
            if predicted_norm and predicted_norm != 'not_found':
                false_positives[predicted_norm] += 1
        
        if is_top3_match:
            top3_correct += 1
        
        # Record for confusion matrix
        confusion_data.append((expected_norm, predicted_norm))
        
        results.append({
            'idx': idx,
            'text': text[:60] + '...' if len(text) > 60 else text,
            'expected': expected,
            'expected_norm': expected_norm,
            'predicted': predicted,
            'predicted_norm': predicted_norm,
            'confidence': confidence,
            'match_rank': match_rank,
            'is_top1': is_top1_match,
            'is_top3': is_top3_match,
            'is_family_match': is_family_match_flag
        })
        
        # Progress indicator
        if idx % 20 == 0:
            print(f"Processed {idx}/{len(test_cases)} verses...")
    
    # Calculate metrics
    top1_accuracy = (top1_correct / total * 100) if total > 0 else 0
    top3_accuracy = (top3_correct / total * 100) if total > 0 else 0
    
    # Calculate family-level accuracy (lenient matching)
    family_correct = sum(1 for r in results if r['is_top1'] or r['is_family_match'])
    family_accuracy = (family_correct / total * 100) if total > 0 else 0
    
    # Per-meter precision/recall
    meter_metrics = {}
    all_meters = set(true_positives.keys()) | set(false_positives.keys()) | set(false_negatives.keys())
    
    for meter in all_meters:
        tp = true_positives[meter]
        fp = false_positives[meter]
        fn = false_negatives[meter]
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support = tp + fn  # Total actual instances
        
        meter_metrics[meter] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }
    
    summary = {
        'total': total,
        'top1_correct': top1_correct,
        'top3_correct': top3_correct,
        'family_correct': family_correct,
        'top1_accuracy': top1_accuracy,
        'top3_accuracy': top3_accuracy,
        'family_accuracy': family_accuracy,
        'meter_metrics': meter_metrics,
        'confusion_data': confusion_data
    }
    
    return results, summary


def print_results(results, summary, show_errors=True):
    """Print formatted evaluation results."""
    
    print("\n" + "=" * 80)
    print("OVERALL ACCURACY")
    print("=" * 80)
    print(f"Total Verses Tested: {summary['total']}")
    print(f"Top-1 Exact Accuracy: {summary['top1_correct']}/{summary['total']} ({summary['top1_accuracy']:.1f}%)")
    print(f"Top-3 Exact Accuracy: {summary['top3_correct']}/{summary['total']} ({summary['top3_accuracy']:.1f}%)")
    print(f"Family-Level Accuracy*: {summary['family_correct']}/{summary['total']} ({summary['family_accuracy']:.1f}%)")
    print()
    print("*Family-Level counts Trishtubh-family (Indravajra, Upendravajra, etc.) and")
    print(" Jagati-family (Vamshastham, Totaka, Bhujangaprayata, etc.) as correct matches.")
    
    # Per-meter breakdown
    print("\n" + "=" * 80)
    print("PER-METER PERFORMANCE")
    print("=" * 80)
    print(f"{'Meter':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("-" * 70)
    
    # Sort by support (most common first)
    sorted_meters = sorted(
        summary['meter_metrics'].items(),
        key=lambda x: x[1]['support'],
        reverse=True
    )
    
    for meter, metrics in sorted_meters:
        if metrics['support'] > 0:  # Only show meters with actual examples
            print(f"{meter:<25} {metrics['precision']:>10.2f} {metrics['recall']:>10.2f} "
                  f"{metrics['f1']:>10.2f} {metrics['support']:>10}")
    
    # Show errors if requested
    if show_errors:
        print("\n" + "=" * 80)
        print("MISCLASSIFIED EXAMPLES")
        print("=" * 80)
        
        errors = [r for r in results if not r['is_top1']]
        
        # Group by expected meter
        errors_by_meter = defaultdict(list)
        for err in errors:
            errors_by_meter[err['expected_norm']].append(err)
        
        for meter, meter_errors in sorted(errors_by_meter.items()):
            print(f"\n{meter.upper()} ({len(meter_errors)} errors):")
            for err in meter_errors[:3]:  # Show first 3 errors per meter
                print(f"  • Text: {err['text']}")
                print(f"    Expected: {err['expected']}, Got: {err['predicted']} (rank: {err['match_rank']})")


def build_confusion_matrix(confusion_data):
    """
    Build and return a confusion matrix from (expected, predicted) pairs.
    Returns matrix as nested dict and list of unique labels.
    """
    # Get unique labels
    labels = sorted(set([x[0] for x in confusion_data] + [x[1] for x in confusion_data]))
    
    # Build matrix
    matrix = defaultdict(lambda: defaultdict(int))
    for expected, predicted in confusion_data:
        matrix[expected][predicted] += 1
    
    return matrix, labels


def print_confusion_matrix(matrix, labels, max_labels=15):
    """Print a text-based confusion matrix."""
    
    # Filter to most common labels if too many
    label_counts = Counter()
    for expected in matrix:
        for predicted in matrix[expected]:
            label_counts[expected] += matrix[expected][predicted]
    
    if len(labels) > max_labels:
        top_labels = [l for l, _ in label_counts.most_common(max_labels)]
        labels = sorted(top_labels)
        print(f"\n(Showing top {max_labels} meters by frequency)")
    
    print("\n" + "=" * 80)
    print("CONFUSION MATRIX (Expected → Predicted)")
    print("=" * 80)
    
    # Also show what each meter was predicted as
    print("\n📊 Prediction Distribution by Expected Meter:\n")
    
    for expected in sorted(label_counts.keys(), key=lambda x: label_counts[x], reverse=True):
        if label_counts[expected] > 0:
            predictions = [(pred, count) for pred, count in matrix[expected].items() if count > 0]
            predictions.sort(key=lambda x: x[1], reverse=True)
            
            pred_str = ", ".join([f"{pred}:{count}" for pred, count in predictions[:5]])
            total = sum(c for _, c in predictions)
            correct = matrix[expected].get(expected, 0)
            acc = (correct / total * 100) if total > 0 else 0
            
            print(f"  {expected:<20} (n={total:>2}, acc={acc:>5.1f}%): {pred_str}")
    
    # Simplified matrix view
    print("\n" + "-" * 80)
    print("Matrix (rows=expected, cols=predicted, showing non-zero cells):")
    print("-" * 80)


def save_results_csv(results, summary, output_path):
    """Save detailed results to CSV file."""
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Index', 'Text', 'Expected', 'Expected_Normalized', 
                         'Predicted', 'Predicted_Normalized', 'Confidence',
                         'Match_Rank', 'Is_Top1', 'Is_Top3'])
        
        for r in results:
            writer.writerow([
                r['idx'], r['text'], r['expected'], r['expected_norm'],
                r['predicted'], r['predicted_norm'], f"{r['confidence']:.2f}",
                r['match_rank'], r['is_top1'], r['is_top3']
            ])
    
    print(f"\nDetailed results saved to: {output_path}")


def save_confusion_matrix_csv(matrix, labels, output_path):
    """Save confusion matrix to CSV file."""
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Header row
        writer.writerow(['Expected\\Predicted'] + labels)
        
        # Data rows
        for expected in labels:
            row = [expected]
            for predicted in labels:
                row.append(matrix[expected][predicted])
            writer.writerow(row)
    
    print(f"Confusion matrix saved to: {output_path}")


def plot_confusion_matrix(matrix, labels, output_path, title="Chandas Identification Confusion Matrix"):
    """Generate and save a visual confusion matrix plot."""
    
    if not PLOT_AVAILABLE:
        print("⚠ Visualization libraries not available. Skipping plot.")
        return
    
    # Filter to labels with at least 1 sample
    active_labels = [l for l in labels if sum(matrix[l].values()) > 0 or 
                     any(matrix[e][l] > 0 for e in labels)]
    
    # Limit to top N for readability
    max_labels = 20
    if len(active_labels) > max_labels:
        # Sort by frequency
        label_freq = Counter()
        for expected in matrix:
            for predicted, count in matrix[expected].items():
                label_freq[expected] += count
        active_labels = [l for l, _ in label_freq.most_common(max_labels)]
    
    # Build matrix as 2D array
    n = len(active_labels)
    cm = np.zeros((n, n), dtype=int)
    
    for i, expected in enumerate(active_labels):
        for j, predicted in enumerate(active_labels):
            cm[i, j] = matrix[expected].get(predicted, 0)
    
    # Create figure
    plt.figure(figsize=(14, 12))
    
    # Plot heatmap
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=active_labels, yticklabels=active_labels,
                cbar_kws={'label': 'Count'})
    
    plt.xlabel('Predicted Meter', fontsize=12)
    plt.ylabel('Expected Meter', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    
    # Rotate labels for readability
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Confusion matrix plot saved to: {output_path}")


###############################################################################
# MAIN
###############################################################################

def main():
    """Main evaluation function."""
    
    # Path to test data
    test_csv = os.path.join(DATA_PATH, 'page 1-47 chanda list - Sheet1.csv')
    
    if not os.path.exists(test_csv):
        print(f"❌ Test data not found: {test_csv}")
        return 1
    
    # Load test data
    print("Loading test data...")
    test_cases = load_test_data(test_csv)
    print(f"Loaded {len(test_cases)} test cases with labeled chandas")
    
    # Get unique meters in test data
    unique_meters = set(normalize_meter_name(tc['expected_chanda']) for tc in test_cases)
    print(f"Unique meters in test data: {len(unique_meters)}")
    
    # Show meter distribution
    meter_dist = Counter(normalize_meter_name(tc['expected_chanda']) for tc in test_cases)
    print("\nMeter distribution (top 10):")
    for meter, count in meter_dist.most_common(10):
        print(f"  {meter}: {count} examples")
    
    # Run evaluation
    print("\n" + "=" * 80)
    print("RUNNING EVALUATION...")
    print("=" * 80)
    
    results, summary = evaluate_model(test_cases, verbose=False)
    
    # Print results
    print_results(results, summary, show_errors=True)
    
    # Build and print confusion matrix
    matrix, labels = build_confusion_matrix(summary['confusion_data'])
    print_confusion_matrix(matrix, labels)
    
    # Save results
    output_dir = os.path.join(DATA_PATH, '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    results_csv = os.path.join(output_dir, 'evaluation_results.csv')
    save_results_csv(results, summary, results_csv)
    
    confusion_csv = os.path.join(output_dir, 'confusion_matrix.csv')
    save_confusion_matrix_csv(matrix, labels, confusion_csv)
    
    # Generate visual plot
    confusion_plot = os.path.join(output_dir, 'confusion_matrix.png')
    plot_confusion_matrix(matrix, labels, confusion_plot)
    
    # Final verdict
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    
    if summary['top1_accuracy'] >= 90:
        print("🎉 EXCELLENT! Top-1 exact accuracy ≥90%")
    elif summary['top1_accuracy'] >= 75:
        print("✓ GOOD! Top-1 exact accuracy ≥75%")
    elif summary['top1_accuracy'] >= 50:
        print("⚠ MODERATE: Top-1 exact accuracy 50-75%")
    else:
        print("⚠ NEEDS IMPROVEMENT: Top-1 exact accuracy <50%")
    
    if summary['family_accuracy'] >= 75:
        print("✓ GOOD family-level recognition (≥75%)")
    
    print(f"\nFinal Scores:")
    print(f"  Top-1 Exact Match:  {summary['top1_accuracy']:.1f}%")
    print(f"  Top-3 Exact Match:  {summary['top3_accuracy']:.1f}%")
    print(f"  Family-Level Match: {summary['family_accuracy']:.1f}%")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
