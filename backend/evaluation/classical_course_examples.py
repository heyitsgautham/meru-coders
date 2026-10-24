"""
Test chandas identification against classical examples from online course PPTs.
These are authentic verses used in traditional Sanskrit education.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chanda import Chanda
from indic_transliteration import sanscript


def test_course_examples():
    """Test all examples from the online chandas course PPTs"""

    # Get data path
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    identifier = Chanda(data_path)

    test_cases = [
        # PPT 5: Indravajrā (11 syllables: ta-ta-ja ga ga)
        {
            'verse': """Śilāpi yāti dyutimantabhāvam
Sparśena yasyāpi jantumaṅgaḥ ।
Uttiṣṭhatē hyātmamupāśritānāṃ
Saṅgaḥ khalu śrēyasi paṇḍitānām ॥""",
            'expected': 'Indravajrā',
            'syllables': 11,
            'pattern': '——U ——U U—U——',
        },
        {
            'verse': """Asti praśastā janalōcanānām
Ānandasandāyiṣu kōsalēṣu ।
Ājñāsamutsāritadānavānāṃ
Rājñāmayōdhyēti purī raghūṇām ॥""",
            'expected': 'Indravajrā',
            'syllables': 11,
        },
        # PPT 6: Upendravajrā (11 syllables: ja-ta-ja ga ga)
        {
            'verse': """Tadēvamēvāsya janādhipasya
Vyavasthitāḥ prakṛtayō'valupyāḥ ।
Na vēttumārhati sa ēva bhēdam
Saṃsargatō hi prabhavanti dōṣāḥ ॥""",
            'expected': 'Upendravajrā',
            'syllables': 11,
            'pattern': 'U—U ——U U—U——',
        },
        {
            'verse': """Mukunda mūrdhnā praṇipatya yācē
Bhavantamēkāntamiyantamartham ।
Avismṛtistvaccharaṇāravindē
Bhavē bhavē mē'stu bhavatprasādāt ॥""",
            'expected': 'Upendravajrā',
            'syllables': 11,
        },
        # PPT 7: Upajāti (mix of Indravajrā and Upendravajrā)
        {
            'verse': """Karāravindēna padāravindam
Mukhāravindē vinivēśayantam ।
Vaṭasya patrasya puṭē śayānam
Bālaṃ mukundaṃ manasā smarāmi ॥""",
            'expected': 'Upajāti',
            'syllables': 11,
        },
        # PPT 8: Rathoddhatā (11 syllables: ra-na-ra la ga)
        {
            'verse': """Nūnamatra vasatē mahēśvarī
Śāśvatī ca samastabhūtaye ।
Adyatāvadavēhi rāghavam
Nirmalā śrutiriva prajānanam ॥""",
            'expected': 'Rathoddhatā',
            'syllables': 11,
            'pattern': '—U— UUU —U— U—',
        },
        {
            'verse': """Cintayāmi harimēva santataṃ
Mandamandahasitānanāmbujam ।
Nandagōpatanayaṃ parātparaṃ
Nāradādimunivṛndavanditam ॥""",
            'expected': 'Rathoddhatā',
            'syllables': 11,
        },
        # PPT 9: Śālinī (11 syllables: ma-ta-ta ga ga, yati 4+7)
        {
            'verse': """Mahēśō vā dēvō vā śivō vā
Sumitraṃ vā bhūpatīrvā yatīrvā ।
Ēkō vāsaḥ pattānē vā vanē vā
Ākāśē vā rāśisvāvāśisvāvāśē ॥""",
            'expected': 'Śālinī',
            'syllables': 11,
            'pattern': '——— ——U ——U——',
        },
        # PPT 10: Vaṃśastha (12 syllables: ja-ta-ja-ra)
        {
            'verse': """Niyōjayā'māsa sa sūnusūnum
Kṣitau kṣitīśaḥ kṣitirakṣaṇāya ।
Tadārabhatyēva sa kālakēlīm
Vinītamānō'vaśamātmanō'pi ॥""",
            'expected': 'Vaṃśastha',
            'syllables': 12,
            'pattern': 'U—U ——U U—U —U—',
        },
        {
            'verse': """Asaṃśayaṃ kṣatraparigrahakṣamā
Yadāryamasyāmabhilāṣi mē manaḥ ।
Satāṃ hi sandēhapadēṣu vastuṣu
Pramāṇamantaḥkaraṇapravṛttayaḥ ॥""",
            'expected': 'Vaṃśastha',
            'syllables': 12,
        },
        # PPT 11: Bhujangaprayātam (12 syllables: ya-ya-ya-ya)
        {
            'verse': """Jalē candrabimbaṃ bhramannēva bhāti
Sphuranmatsyamacchāśubhāśālini ca ।
Na cā'nēna dṛṣṭiḥ śubhā saṃsthitēna
Bhramannapi māyāsamā dṛśyatē hi ॥""",
            'expected': 'Bhujangaprayātam',
            'syllables': 12,
            'pattern': 'U—— U—— U—— U——',
        },
        {
            'verse': """Vinā vēṅkaṭēśaṃ na nāthō na nāthaḥ
Sadā vēṅkaṭēśaṃ smarāmi smarāmi ।
Harē vēṅkaṭēśa prasīda prasīda
Priyam vēṅkaṭēśa prayaccha prayaccha ॥""",
            'expected': 'Bhujangaprayātam',
            'syllables': 12,
        },
        # PPT 12: Toṭakam (12 syllables: sa-sa-sa-sa)
        {
            'verse': """Jayatīndumukundamurāntakam
Śubhadāyakamājñavikāśakam ।
Smarataḥ śravaṇādhvajāyutaiḥ
Janamōhitakēlimanōharaiḥ ॥""",
            'expected': 'Toṭakam',
            'syllables': 12,
            'pattern': 'UU— UU— UU— UU—',
        },
        {
            'verse': """Adharaṃ madhuraṃ vadanaṃ madhuraṃ
Nayanaṃ madhuraṃ hasitaṃ madhuram ।
Hṛdayaṃ madhuraṃ gamanaṃ madhuraṃ
Madhurādhipatērakhilaṃ madhuram ॥""",
            'expected': 'Toṭakam',
            'syllables': 12,
        },
        # PPT 13: Vasantatilakā (14 syllables: ta-bha-ja-ja ga ga)
        {
            'verse': """Prārabhyatē na khalu vighna­bhayēna nīcaiḥ
Prārabhya vighnavihatā viramanti madhyāḥ ।
Vighnaiḥ punaḥ punarapi pratihanyamānāḥ
Prārabdhamuttamajanā na parityajanti ॥""",
            'expected': 'Vasantatilakā',
            'syllables': 14,
            'pattern': '——U —UU U—U U—U——',
        },
        # PPT 14: Mālinī (15 syllables: na-na-ma-ya-ya, yati 8+7)
        {
            'verse': """Sirasi mama sumūrdhni sthāna dēhi kṣamaṇva
Hara mama ca samastān pāpakarmān sarvān ।
Jayati vimaladhīrō vītarāgō viraktaḥ
Mama ca sukhaśāntiṃ sarvakālaṃ prayaccha ॥""",
            'expected': 'Mālinī',
            'syllables': 15,
            'pattern': 'UUU UUU ——— U—— U——',
        },
        {
            'verse': """Sarasijamanuviddhaṃ śaivalēnāpi ramyaṃ
Malinamapi himāṃśōrlakṣma lakṣmīṃ tanōti ।
Iyamadhikamanōjñā valkalēnāpi tanvī
Kimiva hi madhurāṇāṃ maṇḍanaṃ nākṛtīnām ॥""",
            'expected': 'Mālinī',
            'syllables': 15,
        },
        # PPT 15: Pañcacāmara (16 syllables: ja-ra-ja-ra-ja ga)
        {
            'verse': """Śivāya maṅgalaṃ śivāya maṅgalaṃ śivāya maṅgalam
Śivāya maṅgalaṃ śivāya maṅgalaṃ śivāya maṅgalam ।
Śivāya maṅgalaṃ śivāya maṅgalaṃ śivāya maṅgalaṃ
Śivāya maṅgalaṃ śivāya maṅgalaṃ śivāya maṅgalam ॥""",
            'expected': 'Pañcacāmara',
            'syllables': 16,
            'pattern': 'U—U —U— U—U —U— U—U—',
        },
        # PPT 16: Śikhariṇī (17 syllables: ya-ma-na-sa-bha la ga, yati 6+11)
        {
            'verse': """Girāmāhurṇ devīṃ drūhiṇagṛhiṇīmāgamasun
daramvādāṃ rāmaṃ viracitapurāvartanaśivam ।
Śirastasyē vandyam caraṇakamalaṃ cārucaritaṃ
bhajanti prāṇaṃ vai śrutisadanatīrthāśramamathā ॥""",
            'expected': 'Śikhariṇī',
            'syllables': 17,
            'pattern': 'U—— ——— UUU UU— —UU U—',
        },
        # PPT 17: Mandākrāntā (17 syllables: ma-bha-na-ta-ta ga ga, yati 4+6+7)
        {
            'verse': """Kascitkāntāvirahaguruṇā svādhikārātpramattaḥ
Śāpēnāstaṅgamitamahimā varṣabhōgyēṇa bhartuḥ ।
Yakṣaścakrē janakatanayāsnānapuṇyōdakēṣu
Snigdhacchāyātaruṣu vasatiṃ rāmagiryāśramēṣu ॥""",
            'expected': 'Mandākrāntā',
            'syllables': 17,
            'pattern': '——— —UU UUU ——U ——U——',
        },
        {
            'verse': """Prahlādasya vyasanamamitaṃ daityavargasya dambhaṃ
Stambhaṃ vakṣaḥsthalamapi ripōr yaugapadyēna bhēttum ।
Baddhaśraddhaṃ puruṣavapuṣā miśritē viśvadṛṣṭē
Daṃṣṭrārōciḥ viśadabhuvane raṃhasā siṃhavēṣē ॥""",
            'expected': 'Mandākrāntā',
            'syllables': 17,
        },
        # PPT 18: Śārdūlavikrīḍitam (19 syllables: ma-sa-ja-sa-ta-ta ga, yati 12+7)
        {
            'verse': """Janmādyasya yatō'nvayāditarataścārthēṣvabhijñaḥ svarāṭ
Tēnē brahma hṛdā ya ādikavayē muhyanti yatsūrayaḥ ।
Tējōvārimṛdāṃ yathā vinimayō yatra trisargō'mṛṣā
Dhāmnā svēna sadā nirastakuhakaṃ satyaṃ paraṃ dhīmahi ॥""",
            'expected': 'Śārdūlavikrīḍitam',
            'syllables': 19,
            'pattern': '——— UU— U—U UU— ——U ——U—',
        },
        {
            'verse': """Vidyā nāma narasya rūpamadhikaṃ pracchannaguptaṃ dhanam
Vidyā bhōgakarī yaśaḥ sukhakarī vidyā gurūṇāṃ guruḥ ।
Vidyā bandhujano vidēśagamanē vidyā parā dēvatā
Vidyā rājasu pūjyatē na hi dhanaṃ vidyāvihīnaḥ paśuḥ ॥""",
            'expected': 'Śārdūlavikrīḍitam',
            'syllables': 19,
        },
        # PPT 19: Sragdharā (21 syllables: ma-ra-bha-na-ya-ya-ya, yati 7+7+7)
        {
            'verse': """Vidhvaṃsatkṣatravaṃśō mahitagurupadāmbhōruhadvaṇdvadāsaḥ
Satyaṃ Brahmaiva nityaṃ nikhiladuṣṭaniyantā ramābhāgyabhājā ।
Bhrājiṣṇuṃ bhaktavargapraṇayajanaśubhābhīṣṭadātāradēvaṃ
Rājantaṃ Rāmabhadrākhyamakala­guṇaśāliṃ namāmi dvijēndram ॥""",
            'expected': 'Sragdharā',
            'syllables': 21,
            'pattern': '——— —U— —UU UUU U—— U—— U——',
        },
        # PPT 20: Anuṣṭup (8 syllables per pada, special rules for 5th-6th-7th positions)
        {
            'verse': """Mā niṣāda pratiṣṭhāṃ tvam
Agamaḥ śāśvatīḥ samāḥ ।
Yat krauñcamithunādēkam
Avadhīḥ kāmamōhitam ॥""",
            'expected': 'Anuṣṭup',
            'syllables': 8,
            'note': 'First verse ever composed (Vālmīki Rāmāyaṇa)',
        },
        {
            'verse': """Dharmakṣētrē kurukṣētrē
Samavētā yuyutsavaḥ ।
Māmakāḥ pāṇḍavāścaiva
Kimakurvata sañjaya ॥""",
            'expected': 'Anuṣṭup',
            'syllables': 8,
            'note': 'First verse of Bhagavad Gītā',
        },
    ]

    print("=" * 80)
    print("TESTING CLASSICAL COURSE EXAMPLES")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        verse = test['verse']
        expected = test['expected']
        expected_syllables = test['syllables']

        print(f"\n{'=' * 80}")
        print(f"Test {i}: {expected} ({expected_syllables} syllables)")
        if 'note' in test:
            print(f"Note: {test['note']}")
        print(f"{'=' * 80}")

        # Show first line of verse
        first_line = verse.strip().split('\n')[0]
        print(f"Verse: {first_line}...")

        # Convert IAST to Devanagari since process_text has issues with IAST
        verse_dev = sanscript.transliterate(verse, sanscript.IAST, sanscript.DEVANAGARI)

        # Identify - use identify_from_text with verse=True
        full_results = identifier.identify_from_text(verse_dev, verse=True, fuzzy=True)

        # Extract verse results (returns dict with 'result' key containing 'verse' and 'line' keys)
        identified_name = None
        if full_results and 'result' in full_results:
            verse_results = full_results['result'].get('verse', [])
            line_results = full_results['result'].get('line', [])

            if len(verse_results) > 0 and len(line_results) > 0:
                verse_result = verse_results[0]

                # verse_result['chanda'] is a tuple: ([names], score)
                if verse_result.get('chanda') and len(verse_result['chanda'][0]) > 0:
                    identified_names = verse_result['chanda'][0]  # List of meter names
                    confidence = verse_result['chanda'][1]  # Score
                    identified_name = identified_names[0] if identified_names else None

                    # Get syllable count from first line
                    if len(verse_result['lines']) > 0:
                        first_line_result = line_results[verse_result['lines'][0]]
                        identified_syllables = first_line_result['result'].get('length', 0)
                        pattern = ''.join(first_line_result['result'].get('lg', []))

        if identified_name:
            print(f"\n✓ Identified: {identified_name}")
            print(f"  Syllables: {identified_syllables}")
            print(f"  Confidence: {confidence:.1f}")
            print(f"  Pattern: {pattern}")

            # Check if correct
            if expected.lower() in identified_name.lower() or identified_name.lower() in expected.lower():
                print(f"\n✅ PASS - Correctly identified as {expected}")
                passed += 1
            else:
                print(f"\n❌ FAIL - Expected {expected}, got {identified_name}")
                failed += 1

                # Show alternatives
                if len(identified_names) > 1:
                    print("\nAlternatives:")
                    for j, alt_name in enumerate(identified_names[1:4], 2):
                        print(f"  {j}. {alt_name}")
        else:
            print("\n❌ FAIL - No meter identified")
            failed += 1

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed} ({100 * passed // len(test_cases)}%)")
    print(f"Failed: {failed}")
    print(f"{'=' * 80}\n")

    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_course_examples()
    sys.exit(0 if success else 1)
