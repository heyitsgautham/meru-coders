"""Summaries and display strings for identification results.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""

from collections import Counter, defaultdict


class ResultFormatMixin:
    ###########################################################################

    def summarize_results(self, results):
        line_results = results['line']
        verse_results = results['verse']

        match_line_statistics = defaultdict(Counter)
        fuzzy_line_statistics = defaultdict(Counter)
        verse_statistics = defaultdict(Counter)

        counts = defaultdict(int)

        for line_answer in line_results:
            counts['line'] += 1
            line_result = line_answer['result']
            if line_result['found']:
                counts['match_line'] += 1
                chanda_list = line_result['display_chanda'].split('/')
                gana_list = line_result['display_gana'].split('/')

                match_line_statistics['chanda'].update(chanda_list)
                match_line_statistics['gana'].update(gana_list)
            else:
                counts['fuzzy_line'] += 1
                for idx, fuzzy_match in enumerate(line_result['fuzzy']):
                    if idx == 0:
                        counts['mismatch_syllable'] += fuzzy_match['cost']
                    chanda_list = fuzzy_match['display_chanda'].split('/')
                    fuzzy_line_statistics['chanda'].update(chanda_list)
                    break

        for verse_result in verse_results:
            counts['verse'] += 1
            chanda_list, chanda_score = verse_result['chanda']
            if chanda_score == len(verse_result['lines']):
                counts['match_verse'] += 1
            else:
                counts['fuzzy_verse'] += 1
            verse_statistics['chanda'].update(chanda_list)

        return {
            'verse': verse_statistics,
            'line': {
                'fuzzy': fuzzy_line_statistics,
                'match': match_line_statistics,
            },
            'count': counts,
        }

    # def analyse_file(self, file, fuzzy=True, remove_chars=''):
    #     """
    #     Analyses a file and identify Chanda from each line.

    #     @params:
    #         file: path of the input file
    #         remove_chars: characters to be removed

    #     `skt.clean()` is called after removing remove_chars.
    #     Lines are identified using the `skt.split_lines()` function.
    #     """
    #     with open(file, 'r') as f:
    #         content = f.read().translate(str.maketrans('', '', remove_chars))

    #     line_results, verse_results = self.identify_from_text(
    #         content,
    #         verse=True,
    #         fuzzy=True
    #     )

    #     hit = 0
    #     unk = 0
    #     content = []
    #     fuzzy_freq = Counter()
    #     chanda_freq = Counter()
    #     jaati_freq = Counter()
    #     gana_freq = Counter()
    #     matra_freq = Counter()
    #     statistics = defaultdict(Counter)

    #     for line_answer in line_results:
    #         line_result = line_answer['result']

    #         line_chanda = line_result['chanda']
    #         line_jaati = line_result['jaati']
    #         line_gana = line_result['gana']
    #         line_matra = line_result['matra']

    #         hit += line_result['found']
    #         unk += not(line_result['found'])

    #         matra_freq.update([line_matra])
    #         if line_chanda:
    #             line_desc = ' / '.join(line_chanda)
    #             chanda_freq.update(line_chanda)
    #         else:
    #             line_desc = line_gana
    #             gana_freq.update([line_gana])

    #         if fuzzy and line_result['fuzzy']:
    #             line_fuzzy = line_result['fuzzy'][0][0]
    #             fuzzy_freq.update(line_fuzzy)

    #         jaati_freq.update(line_jaati)

    #         content.append(
    #             f"{line_matra:<6}: {line_desc:<20}: {line_answer['line']}"
    #         )

    #     with open(f'{file}.chanda', 'w') as f:
    #         f.write('\n'.join(content))

    #     with open(f'{file}.analysis', 'w') as f:
    #         json.dump(statistics, f, ensure_ascii=False, indent=2)

    #     result = {
    #         'hit': hit,
    #         'unk': unk,
    #         'chanda_freq': chanda_freq,
    #         'fuzzy_freq': fuzzy_freq,
    #         'matra_freq': matra_freq,
    #         'jaati_freq': jaati_freq,
    #         'gana_freq': gana_freq,
    #     }
    #     return result

    ###########################################################################
    # Formatters

    @staticmethod
    def format_chanda_pada(chanda: str, pada: tuple) -> str:
        """Format chanda name with pada information.

        Args:
            chanda: Meter name
            pada: Tuple containing pada number(s), e.g., ('1',), ('1', '2'), or ('',)

        Returns:
            Formatted string with pada info, or just chanda name if no pada
        """
        if not pada or len(pada) == 0:
            return chanda
        if len(pada) == 1:
            return f"{chanda} (पाद {pada[0]})" if pada[0] else chanda
        if len(pada) == 2:
            return f"{chanda} (पाद {pada[0]}-{pada[1]})"
        # Handle 3+ elements (shouldn't happen, but be safe)
        return chanda

    @staticmethod
    def format_line_result(line_result) -> str:
        output_lines = [
            line_result['display_line'],
            f"\tSyllables: {line_result['display_syllables']}",
            f"\tLG: {line_result['display_lg']}",
            f"\tGana: {line_result['display_gana']}",
            (f"\tCounts: {line_result['display_length']} letters, {line_result['display_matra']} morae"),
            f"\tChanda: {line_result['display_chanda']}",
            f"\tJaati: {line_result['display_jaati']} ",
        ]

        # Add prose detection information if available
        if 'is_padya' in line_result:
            padya_status = "पद्य (Poetry)" if line_result['is_padya'] else "गद्य (Prose)"
            output_lines.append(f"\tType: {padya_status}")
            if line_result.get('prose_message'):
                output_lines.append(f"\tNote: {line_result['prose_message']}")

        if line_result['fuzzy']:
            best_match = line_result['fuzzy'][0]
            output_lines.extend(
                [
                    (f"\tFuzzy: {best_match['display_chanda']} ({best_match['similarity']})"),
                    f"\t\t{best_match['suggestion']}",
                ]
            )
        return "\n".join(output_lines)

    @staticmethod
    def format_summary(result_summary) -> str:
        output = []
        if result_summary["verse"]:
            output.extend(["Verse Statistics", "----------------"])
            for idx, (chanda_name, chanda_count) in enumerate(result_summary["verse"]["chanda"].most_common(), start=1):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        output.extend(["Line Statistics", "---------------"])

        if result_summary["line"]["match"]:
            output.append("-- Exact Match")
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["line"]["match"]["chanda"].most_common(), start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        if result_summary["line"]["fuzzy"]:
            output.append("-- Fuzzy Match")
            for idx, (chanda_name, chanda_count) in enumerate(
                result_summary["line"]["fuzzy"]["chanda"].most_common(), start=1
            ):
                output.append(f"{idx:>4}. {chanda_name}: {chanda_count}")
            output.append("")

        counts = result_summary["count"]
        output.extend(
            [
                "Counts",
                "------",
                f"* Total Lines: {counts['line']}",
                f"  - Exact Match: {counts['match_line']}",
                f"  - Fuzzy Match: {counts['fuzzy_line']}",
                f"* Total Verses: {counts['verse']}",
                f"  - Exact Match: {counts['match_verse']}",
                f"  - Fuzzy Match: {counts['fuzzy_verse']}",
                f"* Total Syllables Mismatched: {counts['mismatch_syllable']}",
            ]
        )

        return "\n".join(output)
