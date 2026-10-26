"""Console, CSV and PNG output for confusion_matrix.py."""

import csv
from collections import Counter, defaultdict

# Optional visualization imports
try:
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns

    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False


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
    sorted_meters = sorted(summary['meter_metrics'].items(), key=lambda x: x[1]['support'], reverse=True)

    for meter, metrics in sorted_meters:
        if metrics['support'] > 0:  # Only show meters with actual examples
            print(
                f"{meter:<25} {metrics['precision']:>10.2f} {metrics['recall']:>10.2f} "
                f"{metrics['f1']:>10.2f} {metrics['support']:>10}"
            )

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
        top_labels = [label for label, _ in label_counts.most_common(max_labels)]
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
        writer.writerow(
            [
                'Index',
                'Text',
                'Expected',
                'Expected_Normalized',
                'Predicted',
                'Predicted_Normalized',
                'Confidence',
                'Match_Rank',
                'Is_Top1',
                'Is_Top3',
            ]
        )

        for r in results:
            writer.writerow(
                [
                    r['idx'],
                    r['text'],
                    r['expected'],
                    r['expected_norm'],
                    r['predicted'],
                    r['predicted_norm'],
                    f"{r['confidence']:.2f}",
                    r['match_rank'],
                    r['is_top1'],
                    r['is_top3'],
                ]
            )

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
    active_labels = [
        label for label in labels if sum(matrix[label].values()) > 0 or any(matrix[e][label] > 0 for e in labels)
    ]

    # Limit to top N for readability
    max_labels = 20
    if len(active_labels) > max_labels:
        # Sort by frequency
        label_freq = Counter()
        for expected in matrix:
            for count in matrix[expected].values():
                label_freq[expected] += count
        active_labels = [label for label, _ in label_freq.most_common(max_labels)]

    # Build matrix as 2D array
    n = len(active_labels)
    cm = np.zeros((n, n), dtype=int)

    for i, expected in enumerate(active_labels):
        for j, predicted in enumerate(active_labels):
            cm[i, j] = matrix[expected].get(predicted, 0)

    # Create figure
    plt.figure(figsize=(14, 12))

    # Plot heatmap
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=active_labels,
        yticklabels=active_labels,
        cbar_kws={'label': 'Count'},
    )

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
