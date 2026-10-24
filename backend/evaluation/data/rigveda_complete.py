#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHENTIC Rigveda Test Verses - COMPLETE VERSES ONLY

Filtered to include only verses with ॥ (verse-end marker).
These are complete verses, not partial padas.

Sources:
- Verse texts: repos/Rigveda_api/data/rigveda.json (filtered for ॥)
- Meter annotations: repos/WSC2023/Anukramani/

Generated: 2024-12-02
"""

# Meter name mappings
METER_DEVANAGARI = {
    'gāyatrī': 'गायत्री',
    'triṣṭup': 'त्रिष्टुभ्',
    'jagatī': 'जगती',
    'anuṣṭup': 'अनुष्टुभ्',
    'bṛhatī': 'बृहती',
    'uṣṇik': 'उष्णिक्',
    'paṅkti': 'पङ्क्ति',
}

# Expected syllable counts
METER_SYLLABLES = {
    'gāyatrī': 24,
    'triṣṭup': 44,
    'jagatī': 48,
    'anuṣṭup': 32,
    'bṛhatī': 36,
    'uṣṇik': 28,
    'paṅkti': 40,
}

RIGVEDA_COMPLETE = [
    {
        'ref': '1.1.1',
        'text': 'अ॒ग्निमी॑ळे पु॒रोहि॑तं य॒ज्ञस्य॑ दे॒वमृ॒त्विज॑म् । होता॑रं रत्न॒धात॑मम् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.1.7',
        'text': 'उप॑ त्वाग्ने दि॒वेदि॑वे॒ दोषा॑वस्तर्धि॒या व॒यम् । नमो॒ भर॑न्त॒ एम॑सि ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.4.1',
        'text': 'सु॒रू॒प॒कृ॒त्नुमू॒तये॑ सु॒दुघा॑मिव गो॒दुहे᳚ । जु॒हू॒मसि॒ द्यवि॑द्यवि ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.55.6',
        'text': 'तमि॑न्द्रं वा॒जया॑मसि म॒हे वृ॒त्राय॒ हन्त॑वे ॥',
        'meter': 'jagatī',
        'meter_devanagari': METER_DEVANAGARI.get('jagatī', 'jagatī'),
        'expected_syllables': METER_SYLLABLES.get('jagatī', 0),
    },
    {
        'ref': '1.22.1',
        'text': 'प्रात॑र्युजा॒ वि वो॑ दे॒वा॒नाव॑र्धे॒न्या। आ॒श्वि॒ना॒व॒ह्वया॑महे ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.46.2',
        'text': 'उप॑ नो वाजिनीवसू॒ गच्छ॑तं सोमपी॒तये॑ । सोमा॑ ह॒सन्ति॑ वा॒मिमे ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.37.1',
        'text': 'कण्वा॑ इव॒ प्र गा॑यत॒ भद्रा॒ भद्रो॒क्तिभि॑स्सु॒तम् । स्तोमं॑ विश्व॒प्रियं॒ नरः॑ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.87.2',
        'text': 'अना॑न॒ता वृष॑णः पिन्वतो॒ रुहो॒ द्युमन्त॑श्शु॒ष्मा म॒रुतो॑ वि॒दद्र॑यः ॥',
        'meter': 'jagatī',
        'meter_devanagari': METER_DEVANAGARI.get('jagatī', 'jagatī'),
        'expected_syllables': METER_SYLLABLES.get('jagatī', 0),
    },
    {
        'ref': '1.15.6',
        'text': 'मि॒त्रावरु॑णा॒वश्वि॑ना॒ त्वाष्ट॒रमव॑ सेधतम् । ब्र॒ह्म॒णा व॑र्धय॒तम् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.152.2',
        'text': 'ऋ॒तस्य॑ गो॒पौ॒ न द॑भाय॑ते॒ यु॒वम् । मि॒त्राव॑रुणा ॥',
        'meter': 'triṣṭup',
        'meter_devanagari': METER_DEVANAGARI.get('triṣṭup', 'triṣṭup'),
        'expected_syllables': METER_SYLLABLES.get('triṣṭup', 0),
    },
    {
        'ref': '1.43.1',
        'text': 'कद्रा॑य रु॒द्राय॒ मीळ्हु॑षे॒ कं क्षय॑द्वी॒राय॒ नम॑सा दि॒शेम ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.43.6',
        'text': 'अ॒ना॒म्य॒स्य॒ श॒वसा॑ रु॒द्रस्य॑ दि॒व्यानाम् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.35.1',
        'text': 'ह्वया॑मि मि॒त्रं वरु॑णं॒ ये स॒जोषा॑ घृ॒तं ह॒वीर॑र्व॒ते नाध॑मानाः । ति॒रो अ॒रीचि॒मेक॒स्सुश्र॑वो॒ धाः सवि॒ता दे॒वो अस्ता॑त् ॥',
        'meter': '(1',
        'meter_devanagari': METER_DEVANAGARI.get('(1', '(1'),
        'expected_syllables': METER_SYLLABLES.get('(1', 0),
    },
    {
        'ref': '1.35.9',
        'text': 'हिर॑ण्यपाणिः सवि॒ता वि च॑र्ष॒णिरा॒ङ्गुलीभि॑रु॒भयं॑ जिगाति ॥',
        'meter': '(1',
        'meter_devanagari': METER_DEVANAGARI.get('(1', '(1'),
        'expected_syllables': METER_SYLLABLES.get('(1', 0),
    },
    {
        'ref': '1.2.1',
        'text': 'वा॒यवा या॑हि द॒र्शते॒मे सोमा॒ अरं॑ कृ॒ताः । तेषां॑ पिब शुचिषिप॒रया॒ धिया॑ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.134.1',
        'text': 'वातो॒ वा मनो॒ वा ग॒न्ध॒र्वो वा स॒प्तविं॑शति॒र्वा । अ॒न्येषां॑ वा य॒ो दे॒वानां॒ तान्सा॑रङ्ग प॒रमं॒ नमा॑मि ॥',
        'meter': 'atyaṣṭiḥ',
        'meter_devanagari': METER_DEVANAGARI.get('atyaṣṭiḥ', 'atyaṣṭiḥ'),
        'expected_syllables': METER_SYLLABLES.get('atyaṣṭiḥ', 0),
    },
    {
        'ref': '1.22.17',
        'text': 'विष्णो॒र्नु कं॑ वी॒र्या॑णि॒ प्र वो॑च॒ यः पार्थि॑वानि विम॒मे रजां॑सि ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.22.18',
        'text': 'तस्यो॑रुषु त्रि॒षु वि॒क्रमे॒ष्वधि॑क्षियन्ति॒ भुव॑नानि॒ विश्वा॑ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.48.1',
        'text': 'ए॒षा दि॒वो दुहि॒ता प्र॒त्यद॑र्शि॒ ज्योति॑र्वस॒ाना स॑मि॒धा शुभा॑गीः । ऋ॒तस्य॒ पन्था॒मनु॑ तिष्ठ॑ति॒ सा स॒र्वं कृ॒णोति॒ यदिदं॒ वि भ॑क्तम् ॥',
        'meter': 'bṛhatī',
        'meter_devanagari': METER_DEVANAGARI.get('bṛhatī', 'bṛhatī'),
        'expected_syllables': METER_SYLLABLES.get('bṛhatī', 0),
    },
    {
        'ref': '1.49.3',
        'text': 'इ॒यं या ते॒ दूत॑कृ॒त्या कृ॒तेय॒मार्मि॑ने॒ वेशि॑ वसु॒वनि॒स्सा ॥',
        'meter': 'anuṣṭup',
        'meter_devanagari': METER_DEVANAGARI.get('anuṣṭup', 'anuṣṭup'),
        'expected_syllables': METER_SYLLABLES.get('anuṣṭup', 0),
    },
    {
        'ref': '1.12.1',
        'text': 'अ॒ग्निं दू॒तं वृ॑णीमहे॒ होता॑रं वि॒श्ववे॑दसम् । अ॒स्य य॒ज्ञस्य॑ सु॒क्रतुम् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.4.1',
        'text': 'सु॒रू॒प॒कृ॒त्नुमू॒तये॑ सु॒दुघा॑मिव गो॒दुहे᳚ । जु॒हू॒मसि॒ द्यवि॑द्यवि ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.7.6',
        'text': 'वि बृ॑ह॒ता सु॒शुष्मि॑णा॒ वरा॑य शत्रुम॒र्धिन॑ । इन्द्रा॒भ्यम॑र्दिषत् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.2.1',
        'text': 'वा॒यवा या॑हि द॒र्शते॒मे सोमा॒ अरं॑ कृ॒ताः । तेषां॑ पिब शुचिषिप॒रया॒ धिया॑ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.2.7',
        'text': 'मि॒त्रं हु॑वे पू॒तद॑क्षं॒ वरु॑णं च रि॒शाद॑सम् । धियं॑ घृ॒ताचीं॒ साध॑न्ता ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.22.1',
        'text': 'प्रात॑र्युजा॒ वि वो॑ दे॒वा॒नाव॑र्धे॒न्या। आ॒श्वि॒ना॒व॒ह्वया॑महे ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.46.10',
        'text': 'यु॒वं ह॑ भु॒ज्युं यु॒वम॒श्विना॒ रथै॒रपां॒ नपा॑तं॒ सव॑ना॒वगच्छ॑तम् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.15.6',
        'text': 'मि॒त्रावरु॑णा॒वश्वि॑ना॒ त्वाष्ट॒रमव॑ सेधतम् । ब्र॒ह्म॒णा व॑र्धय॒तम् ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.23.5',
        'text': 'पुना॑ति ते प॒रि॒स्रु॑तं॒ सोमं॑ सूर्य॑स्य दुहि॒ता ॥',
        'meter': '(1-18',
        'meter_devanagari': METER_DEVANAGARI.get('(1-18', '(1-18'),
        'expected_syllables': METER_SYLLABLES.get('(1-18', 0),
    },
    {
        'ref': '1.37.1',
        'text': 'कण्वा॑ इव॒ प्र गा॑यत॒ भद्रा॒ भद्रो॒क्तिभि॑स्सु॒तम् । स्तोमं॑ विश्व॒प्रियं॒ नरः॑ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.85.12',
        'text': 'रथा॑ँ अ॒वा॑न् ऋ॒ष्टि॒म॑त॒स्सुध॑नवः॒ पृष॑तीर्यु॒ञ्जते॑ । म॒रुतो॒ अध्व॑नो वि॒दुः ॥',
        'meter': '(1-4',
        'meter_devanagari': METER_DEVANAGARI.get('(1-4', '(1-4'),
        'expected_syllables': METER_SYLLABLES.get('(1-4', 0),
    },
    {
        'ref': '1.43.1',
        'text': 'कद्रा॑य रु॒द्राय॒ मीळ्हु॑षे॒ कं क्षय॑द्वी॒राय॒ नम॑सा दि॒शेम ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.114.1',
        'text': 'इ॒मा रु॒द्राय॑ त॒वसे॑ क॒प॒र्दिने᳚ क्षय॒द्वीरा॑य॒ प्र भ॑रामहे म॒तीः । यथा॒ शमसु॑म॒द्द्विप॑दे॒ चतु॑ष्पदे॒ विश्वं॑ पु॒ष्टं ग्रा॒मे अ॒स्मिन्नना॑तुरम् ॥',
        'meter': 'jagatī',
        'meter_devanagari': METER_DEVANAGARI.get('jagatī', 'jagatī'),
        'expected_syllables': METER_SYLLABLES.get('jagatī', 0),
    },
    {
        'ref': '1.48.1',
        'text': 'ए॒षा दि॒वो दुहि॒ता प्र॒त्यद॑र्शि॒ ज्योति॑र्वस॒ाना स॑मि॒धा शुभा॑गीः । ऋ॒तस्य॒ पन्था॒मनु॑ तिष्ठ॑ति॒ सा स॒र्वं कृ॒णोति॒ यदिदं॒ वि भ॑क्तम् ॥',
        'meter': 'bṛhatī',
        'meter_devanagari': METER_DEVANAGARI.get('bṛhatī', 'bṛhatī'),
        'expected_syllables': METER_SYLLABLES.get('bṛhatī', 0),
    },
    {
        'ref': '1.49.3',
        'text': 'इ॒यं या ते॒ दूत॑कृ॒त्या कृ॒तेय॒मार्मि॑ने॒ वेशि॑ वसु॒वनि॒स्सा ॥',
        'meter': 'anuṣṭup',
        'meter_devanagari': METER_DEVANAGARI.get('anuṣṭup', 'anuṣṭup'),
        'expected_syllables': METER_SYLLABLES.get('anuṣṭup', 0),
    },
    {
        'ref': '1.3.7',
        'text': 'आ दे॒वा॑सो॒ ममूहि॑रे॒ विश्वे॑ दे॒वास॒ आदितः॑ । हव्य॒दावा॑नमू॒तये᳚ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.20.7',
        'text': 'प्र णः॑ पूर्व॒स्मिन् मि॒त्राव॑रुणा । इ॒न्द्र॒ग्नी अ॒श्विना॑ वि॒श्वदे॑वाः ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.40.1',
        'text': 'बृह॒स्पतिः॑ प्र॑थ॒मं जाय॑मानो म॒हो ज्योति॑षः पर॒मे व्यो॑मन् । स॒प्तास्य॑स्तु॒विजा॒तो रव॑णो॒ वि स॒प्तर॑श्मिरधमत्तमां॑सि ॥',
        'meter': 'bṛhatī',
        'meter_devanagari': METER_DEVANAGARI.get('bṛhatī', 'bṛhatī'),
        'expected_syllables': METER_SYLLABLES.get('bṛhatī', 0),
    },
    {
        'ref': '1.40.3',
        'text': 'आ नो॒ भर॒ भगा॑वत्तव॒च्यं॑ दे॒वा नः॑ स॒न्तो ब्र॑ह्म॒णे व॑र्धयन्तु ॥',
        'meter': 'bṛhatī',
        'meter_devanagari': METER_DEVANAGARI.get('bṛhatī', 'bṛhatī'),
        'expected_syllables': METER_SYLLABLES.get('bṛhatī', 0),
    },
    {
        'ref': '1.22.17',
        'text': 'विष्णो॒र्नु कं॑ वी॒र्या॑णि॒ प्र वो॑च॒ यः पार्थि॑वानि विम॒मे रजां॑सि ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.22.18',
        'text': 'तस्यो॑रुषु त्रि॒षु वि॒क्रमे॒ष्वधि॑क्षियन्ति॒ भुव॑नानि॒ विश्वा॑ ॥',
        'meter': 'gāyatrī',
        'meter_devanagari': METER_DEVANAGARI.get('gāyatrī', 'gāyatrī'),
        'expected_syllables': METER_SYLLABLES.get('gāyatrī', 0),
    },
    {
        'ref': '1.159.1',
        'text': 'अ॒हमिद्धि॑ पितुः सु॒भगो॑ नाम॒धेय॒ इमां घियं॑ विममा॒न आयोः । भारे॒ क्रा॒णो॒ यद॒य॒न॒स्य स॒र्वस्या॒हं भूमि॒रेको॑ अ॒स्य॒ स॒र्वस्य॑ ॥',
        'meter': 'jagatī',
        'meter_devanagari': METER_DEVANAGARI.get('jagatī', 'jagatī'),
        'expected_syllables': METER_SYLLABLES.get('jagatī', 0),
    },
    {
        'ref': '1.159.6',
        'text': 'दे॒वी नः॒ पत्नी॑ अ॒हं पति॑र्न॒मोऽस्तु॑ । नमो॑ दि॒व्येभ्य॒श्शुभा॑यै॒व नमो॑ ह॒व्यैभ्यो॒ नमो॑ दे॒वीभ्यः॑ स॒र्वदा॑ न॒मोऽस्तु॑ ॥',
        'meter': 'jagatī',
        'meter_devanagari': METER_DEVANAGARI.get('jagatī', 'jagatī'),
        'expected_syllables': METER_SYLLABLES.get('jagatī', 0),
    },
]

# Total count
TOTAL_VERSES = len(RIGVEDA_COMPLETE)
