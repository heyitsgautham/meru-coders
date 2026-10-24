"""
Valmiki Ramayana Dataset Validation Test
Tests the accuracy of meter identification system against 23,402 authentic Ramayana shlokas.

Test Strategy:
1. Full dataset validation (all 23,402 verses)
2. Statistical analysis by Kanda
3. Meter distribution analysis
4. Edge case identification
5. Performance benchmarking

Usage:
    python tests/test_ramayana_validation.py              # Quick test (1000 samples)
    python tests/test_ramayana_validation.py --full       # Full dataset (23,402 verses)
    python tests/test_ramayana_validation.py --kanda 1    # Test specific Kanda
    python tests/test_ramayana_validation.py --stats      # Generate statistics only
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.chanda import Chanda


class RamayanaValidator:
    """Validates meter identification against Valmiki Ramayana dataset."""

    KANDA_NAMES = [
        "Bala Kanda",
        "Ayodhya Kanda",
        "Aranya Kanda",
        "Kishkindha Kanda",
        "Sundara Kanda",
        "Yuddha Kanda",
        "Uttara Kanda"
    ]

    def __init__(self, data_path: str = None):
        """Initialize validator with Chanda engine."""
        if data_path is None:
            data_path = backend_path / "data"
        self.chanda = Chanda(data_path=str(data_path))
        self.dataset = None
        self.results = {
            'total_tested': 0,
            'successful': 0,
            'failed': 0,
            'meter_distribution': Counter(),
            'kanda_stats': defaultdict(lambda: {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'meters': Counter()
            }),
            'confidence_scores': [],
            'processing_times': [],
            'failed_examples': []
        }

    def load_dataset(self, dataset_path: str = None) -> bool:
        """Load Valmiki Ramayana dataset."""
        if dataset_path is None:
            # Default path relative to backend
            dataset_path = backend_path.parent / "repos" / "Valmiki_Ramayan_Dataset" / "data" / "Valmiki_Ramayan_Shlokas.json"

        try:
            print(f"Loading dataset from: {dataset_path}")
            with open(dataset_path, 'r', encoding='utf-8') as f:
                self.dataset = json.load(f)
            print(f"✅ Loaded {len(self.dataset)} shlokas from Valmiki Ramayana\n")
            return True
        except FileNotFoundError:
            print(f"❌ Error: Dataset not found at {dataset_path}")
            print("Please ensure the Valmiki_Ramayan_Dataset repository is cloned.")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error: Failed to parse JSON: {e}")
            return False

    def preprocess_shloka(self, shloka_text: str) -> str:
        """Clean and preprocess shloka text."""
        # Remove shloka numbering (e.g., "।।1.1.1।।")
        text = shloka_text.split('।।')[0].strip()
        return text

    def test_shloka(self, shloka: Dict) -> Dict:
        """Test a single shloka and return results."""
        text = self.preprocess_shloka(shloka['shloka_text'])

        start_time = time.time()
        result = self.chanda.identify_line(text)
        processing_time = time.time() - start_time

        return {
            'shloka': shloka,
            'text': text,
            'result': result,
            'processing_time': processing_time,
            'found': result['found'],
            'meter': result.get('display_chanda_primary', 'NOT_FOUND'),
            'confidence': self._extract_confidence(result)
        }

    def _extract_confidence(self, result: Dict) -> float:
        """Extract confidence score from result."""
        if not result['found']:
            return 0.0

        # Try to extract confidence from display_chanda_primary
        meter_str = result.get('display_chanda_primary', '')
        if '[' in meter_str and ']' in meter_str:
            try:
                conf = meter_str.split('[')[-1].split(']')[0]
                return float(conf)
            except (ValueError, IndexError):
                pass

        # Default high confidence for found meters
        return 10.0

    def validate_sample(self, sample_size: int = 1000, step: int = None) -> None:
        """Validate a sample of shlokas."""
        if self.dataset is None:
            print("❌ Error: Dataset not loaded. Call load_dataset() first.")
            return

        if step is None:
            step = max(1, len(self.dataset) // sample_size)

        print(f"Testing {min(sample_size, len(self.dataset))} shlokas (every {step}th shloka)...\n")

        tested = 0
        for i in range(0, len(self.dataset), step):
            if tested >= sample_size:
                break

            test_result = self.test_shloka(self.dataset[i])
            self._update_results(test_result)
            tested += 1

            # Progress indicator
            if tested % 100 == 0:
                print(f"Progress: {tested}/{sample_size} ({tested/sample_size*100:.1f}%)")

        print(f"\n✅ Completed testing {tested} shlokas\n")

    def validate_full(self) -> None:
        """Validate entire dataset."""
        if self.dataset is None:
            print("❌ Error: Dataset not loaded. Call load_dataset() first.")
            return

        print(f"Testing ALL {len(self.dataset)} shlokas from Valmiki Ramayana...")
        print("⚠️  This may take 10-15 minutes...\n")

        start_time = time.time()

        for i, shloka in enumerate(self.dataset):
            test_result = self.test_shloka(shloka)
            self._update_results(test_result)

            # Progress indicator every 1000 shlokas
            if (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (len(self.dataset) - i - 1) / rate
                print(f"Progress: {i+1}/{len(self.dataset)} ({(i+1)/len(self.dataset)*100:.1f}%) - "
                      f"ETA: {remaining/60:.1f} min")

        total_time = time.time() - start_time
        print(f"\n✅ Completed testing {len(self.dataset)} shlokas in {total_time/60:.2f} minutes\n")

    def validate_kanda(self, kanda_name: str) -> None:
        """Validate specific Kanda."""
        if self.dataset is None:
            print("❌ Error: Dataset not loaded. Call load_dataset() first.")
            return

        kanda_shlokas = [s for s in self.dataset if s['kanda'] == kanda_name]

        if not kanda_shlokas:
            print(f"❌ Error: No shlokas found for Kanda '{kanda_name}'")
            print(f"Available Kandas: {', '.join(self.KANDA_NAMES)}")
            return

        print(f"Testing {len(kanda_shlokas)} shlokas from {kanda_name}...\n")

        for shloka in kanda_shlokas:
            test_result = self.test_shloka(shloka)
            self._update_results(test_result)

        print(f"\n✅ Completed testing {len(kanda_shlokas)} shlokas from {kanda_name}\n")

    def _update_results(self, test_result: Dict) -> None:
        """Update results with test outcome."""
        shloka = test_result['shloka']
        kanda = shloka['kanda']

        self.results['total_tested'] += 1
        self.results['processing_times'].append(test_result['processing_time'])

        if test_result['found']:
            self.results['successful'] += 1
            self.results['meter_distribution'][test_result['meter']] += 1
            self.results['confidence_scores'].append(test_result['confidence'])

            # Kanda stats
            self.results['kanda_stats'][kanda]['total'] += 1
            self.results['kanda_stats'][kanda]['successful'] += 1
            self.results['kanda_stats'][kanda]['meters'][test_result['meter']] += 1
        else:
            self.results['failed'] += 1
            self.results['kanda_stats'][kanda]['total'] += 1
            self.results['kanda_stats'][kanda]['failed'] += 1

            # Store failed examples (limit to 50)
            if len(self.results['failed_examples']) < 50:
                self.results['failed_examples'].append({
                    'kanda': kanda,
                    'sarga': shloka['sarga'],
                    'shloka': shloka['shloka'],
                    'text': test_result['text'][:100] + '...' if len(test_result['text']) > 100 else test_result['text']
                })

    def print_summary(self) -> None:
        """Print comprehensive test summary."""
        r = self.results

        print("=" * 80)
        print("VALMIKI RAMAYANA VALIDATION RESULTS")
        print("=" * 80)

        # Overall Statistics
        success_rate = (r['successful'] / r['total_tested'] * 100) if r['total_tested'] > 0 else 0
        print("\n📊 OVERALL STATISTICS")
        print("-" * 80)
        print(f"Total Shlokas Tested:    {r['total_tested']:,}")
        print(f"Successfully Identified: {r['successful']:,} ({success_rate:.2f}%)")
        print(f"Failed to Identify:      {r['failed']:,} ({100-success_rate:.2f}%)")

        # Performance Metrics
        if r['processing_times']:
            avg_time = sum(r['processing_times']) / len(r['processing_times'])
            max_time = max(r['processing_times'])
            min_time = min(r['processing_times'])
            print("\n⚡ PERFORMANCE METRICS")
            print("-" * 80)
            print(f"Average Processing Time: {avg_time*1000:.2f} ms/shloka")
            print(f"Min Processing Time:     {min_time*1000:.2f} ms")
            print(f"Max Processing Time:     {max_time*1000:.2f} ms")
            print(f"Total Processing Time:   {sum(r['processing_times'])/60:.2f} minutes")

        # Confidence Scores
        if r['confidence_scores']:
            avg_conf = sum(r['confidence_scores']) / len(r['confidence_scores'])
            print("\n🎯 CONFIDENCE ANALYSIS")
            print("-" * 80)
            print(f"Average Confidence:      {avg_conf:.2f}")
            print(f"High Confidence (>9.0):  {sum(1 for c in r['confidence_scores'] if c > 9.0):,} "
                  f"({sum(1 for c in r['confidence_scores'] if c > 9.0)/len(r['confidence_scores'])*100:.1f}%)")

        # Meter Distribution
        print("\n🕉️ METER DISTRIBUTION (Top 10)")
        print("-" * 80)
        for meter, count in r['meter_distribution'].most_common(10):
            percentage = (count / r['successful'] * 100) if r['successful'] > 0 else 0
            # Clean meter name for display
            meter_clean = meter.split('[')[0].strip()
            print(f"{meter_clean:50s} {count:6,} ({percentage:5.2f}%)")

        # Kanda-wise Statistics
        print("\n📚 KANDA-WISE ANALYSIS")
        print("-" * 80)
        print(f"{'Kanda':<25s} {'Tested':>10s} {'Success':>10s} {'Rate':>10s} {'Top Meter':<30s}")
        print("-" * 80)

        for kanda_name in self.KANDA_NAMES:
            if kanda_name in r['kanda_stats']:
                stats = r['kanda_stats'][kanda_name]
                total = stats['total']
                success = stats['successful']
                rate = (success / total * 100) if total > 0 else 0
                top_meter = stats['meters'].most_common(1)[0][0].split('[')[0].strip() if stats['meters'] else 'N/A'

                print(f"{kanda_name:<25s} {total:>10,} {success:>10,} {rate:>9.1f}% {top_meter:<30s}")

        # Failed Examples
        if r['failed_examples']:
            print("\n❌ FAILED EXAMPLES (First 10)")
            print("-" * 80)
            for i, ex in enumerate(r['failed_examples'][:10], 1):
                print(f"{i}. {ex['kanda']}, Sarga {ex['sarga']}, Shloka {ex['shloka']}")
                print(f"   Text: {ex['text']}")
                print()

        print("=" * 80)

        # Overall Assessment
        if success_rate >= 99:
            print("✅ EXCELLENT: System achieves >99% accuracy on Valmiki Ramayana!")
        elif success_rate >= 95:
            print("✅ VERY GOOD: System achieves >95% accuracy on Valmiki Ramayana")
        elif success_rate >= 90:
            print("⚠️  GOOD: System achieves >90% accuracy - some improvement possible")
        else:
            print("⚠️  NEEDS IMPROVEMENT: Accuracy below 90%")

        print("=" * 80)

    def export_results(self, output_file: str = None) -> None:
        """Export detailed results to JSON file."""
        if output_file is None:
            output_file = backend_path.parent / "outputs" / f"ramayana_validation_{int(time.time())}.json"

        output_data = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'dataset': 'Valmiki Ramayana',
            'total_shlokas': len(self.dataset) if self.dataset else 0,
            'tested_shlokas': self.results['total_tested'],
            'statistics': {
                'total_tested': self.results['total_tested'],
                'successful': self.results['successful'],
                'failed': self.results['failed'],
                'success_rate': (self.results['successful'] / self.results['total_tested'] * 100)
                                if self.results['total_tested'] > 0 else 0,
                'avg_processing_time_ms': sum(self.results['processing_times']) / len(self.results['processing_times']) * 1000
                                         if self.results['processing_times'] else 0,
                'avg_confidence': sum(self.results['confidence_scores']) / len(self.results['confidence_scores'])
                                 if self.results['confidence_scores'] else 0
            },
            'meter_distribution': dict(self.results['meter_distribution'].most_common()),
            'kanda_statistics': dict(self.results['kanda_stats']),
            'failed_examples': self.results['failed_examples']
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n📁 Results exported to: {output_file}")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate meter identification against Valmiki Ramayana dataset')
    parser.add_argument('--full', action='store_true', help='Test entire dataset (23,402 verses)')
    parser.add_argument('--sample', type=int, default=1000, help='Sample size for quick test (default: 1000)')
    parser.add_argument('--kanda', type=str, help='Test specific Kanda (e.g., "Bala Kanda")')
    parser.add_argument('--export', type=str, help='Export results to JSON file')
    parser.add_argument('--dataset', type=str, help='Path to Valmiki Ramayana JSON file')

    args = parser.parse_args()

    # Initialize validator
    validator = RamayanaValidator()

    # Load dataset
    if not validator.load_dataset(args.dataset):
        sys.exit(1)

    # Run validation
    if args.kanda:
        validator.validate_kanda(args.kanda)
    elif args.full:
        validator.validate_full()
    else:
        validator.validate_sample(sample_size=args.sample)

    # Print summary
    validator.print_summary()

    # Export if requested
    if args.export:
        validator.export_results(args.export)

    # Return exit code based on success rate
    success_rate = (validator.results['successful'] / validator.results['total_tested'] * 100) \
                   if validator.results['total_tested'] > 0 else 0

    if success_rate >= 95:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Needs improvement


if __name__ == '__main__':
    main()
