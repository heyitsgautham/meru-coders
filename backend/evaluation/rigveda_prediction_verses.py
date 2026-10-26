"""The labelled Rigveda verses rigveda_prediction.py checks the engine against."""

RIGVEDA_TEST_VERSES = [
    # ==========================================================================
    # MANDALA 1 - GĀYATRĪ (24 syllables = 3×8)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 1,
        'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवं ऋत्विजम् ।\nहोतारं रत्नधातमम् ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Opening verse of Rig Veda - Agni Sukta',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 2,
        'text': 'अग्निः पूर्वेभिर्ऋषिभिः ईड्यो नूतनैरुत ।\nस देवानेह वक्षति ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 2',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 3,
        'text': 'अग्निना रयिमश्नवत् पोषमेव दिवेदिवे ।\nयशसं वीरवत्तमम् ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 3',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 4,
        'text': 'अग्ने यं यज्ञमध्वरं विश्वतः परिभूरसि ।\nस इद्देवेषु गच्छति ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 4',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 5,
        'text': 'अग्निर्होता कविक्रतुः सत्यश्चित्रश्रवस्तमः ।\nदेवो देवेभिरा गमत् ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 5',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 6,
        'text': 'यदङ्ग दाशुषे त्वमग्ने भद्रं करिष्यसि ।\nतवेत्तत्सत्यमङ्गिरः ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 6',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 7,
        'text': 'उप त्वाग्ने दिवेदिवे दोषावस्तर्धिया वयम् ।\nनमो भरन्त एमसि ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 7',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 8,
        'text': 'राजन्तमध्वराणां गोपां ऋतस्य दीदिविम् ।\nवर्धमानं स्वे दमे ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 8',
    },
    {
        'mandala': 1,
        'hymn': 1,
        'verse': 9,
        'text': 'स नः पितेव सूनवे ऽग्ने सूपायनो भव ।\nसचस्वा नः स्वस्तये ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'Agni Sukta verse 9 (final)',
    },
    # ==========================================================================
    # MANDALA 1 - TRIṢṬUBH (44 syllables = 4×11)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 32,
        'verse': 1,
        'text': 'इन्द्रस्य नु वीर्याणि प्र वोचं यानि चकार प्रथमानि वज्री ।\nअहन्नहिमन्वपस्ततर्द प्र वक्षणा अभिनत्पर्वतानाम् ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Indra-Vritra Sukta - famous creation hymn',
    },
    {
        'mandala': 1,
        'hymn': 32,
        'verse': 2,
        'text': 'अहन्नहिं पर्वते शिश्रियाणं त्वष्टास्मै वज्रं स्वर्यं ततक्ष ।\nवाश्रा इव धेनवः स्यन्दमाना अञ्जः समुद्रमव जग्मुरापः ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Indra-Vritra Sukta verse 2',
    },
    {
        'mandala': 1,
        'hymn': 32,
        'verse': 3,
        'text': 'वृषायमाणोऽवृणीत सोमं त्रिकद्रुकेष्वपिबत्सुतस्य ।\nआ सायकं मघवादत्त वज्रमहन्नेनं प्रथमजामहीनाम् ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Indra-Vritra Sukta verse 3',
    },
    {
        'mandala': 1,
        'hymn': 154,
        'verse': 1,
        'text': 'विष्णोर्नु कं वीर्याणि प्र वोचं यः पार्थिवानि विममे रजांसि ।\nयो अस्कभायदुत्तरं सधस्थं विचक्रमाणस्त्रेधोरुगायः ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Vishnu Sukta - Three strides of Vishnu',
    },
    {
        'mandala': 1,
        'hymn': 154,
        'verse': 2,
        'text': 'प्र तद्विष्णुः स्तवते वीर्येण मृगो न भीमः कुचरो गिरिष्ठाः ।\nयस्योरुषु त्रिषु विक्रमणेष्वधिक्षियन्ति भुवनानि विश्वा ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Vishnu Sukta verse 2',
    },
    {
        'mandala': 1,
        'hymn': 154,
        'verse': 3,
        'text': 'प्र विष्णवे शूषमेतु मन्म गिरिक्षित उरुगायाय वृष्णे ।\nय इदं दीर्घं प्रयतं सधस्थमेको विममे त्रिभिरित्पदेभिः ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Vishnu Sukta verse 3',
    },
    # ==========================================================================
    # MANDALA 1 - JAGATĪ (48 syllables = 4×12)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 164,
        'verse': 1,
        'text': 'अस्य वामस्य पलितस्य होतुस्तस्य भ्राता मध्यमो अस्त्यश्नः ।\nतृतीयो भ्राता घृतपृष्ठो अस्यात्रापश्यं विश्पतिं सप्तपुत्रम् ॥',
        'meter': 'jagatī',
        'source': 'sacred-texts',
        'notes': 'Asya Vamasya Sukta - famous riddle hymn',
    },
    {
        'mandala': 1,
        'hymn': 164,
        'verse': 20,
        'text': 'द्वा सुपर्णा सयुजा सखाया समानं वृक्षं परिषस्वजाते ।\nतयोरन्यः पिप्पलं स्वाद्वत्त्यनश्नन्नन्यो अभिचाकशीति ॥',
        'meter': 'jagatī',
        'source': 'sacred-texts',
        'notes': 'Two birds on a tree - famous philosophical verse',
    },
    {
        'mandala': 1,
        'hymn': 164,
        'verse': 46,
        'text': 'इन्द्रं मित्रं वरुणमग्निमाहुरथो दिव्यः स सुपर्णो गरुत्मान् ।\nएकं सद्विप्रा बहुधा वदन्त्यग्निं यमं मातरिश्वानमाहुः ॥',
        'meter': 'jagatī',
        'source': 'sacred-texts',
        'notes': 'Ekam Sat - One Truth, sages call it by many names',
    },
    # ==========================================================================
    # MANDALA 1 - ANUṢṬUBH (32 syllables = 4×8)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 89,
        'verse': 1,
        'text': 'आ नो भद्राः क्रतवो यन्तु विश्वतोऽदब्धासो अपरीतास उद्भिदः ।\nदेवा नो यथा सदमिद्वृधे असन्नप्रायुवो रक्षितारो दिवेदिवे ॥',
        'meter': 'triṣṭubh',  # Actually mixed meter in some recensions
        'source': 'sacred-texts',
        'notes': 'Vishvedevah Sukta - Blessings prayer',
    },
    # ==========================================================================
    # MANDALA 3 - GĀYATRĪ (Famous verses)
    # ==========================================================================
    {
        'mandala': 3,
        'hymn': 62,
        'verse': 10,
        'text': 'तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि ।\nधियो यो नः प्रचोदयात् ॥',
        'meter': 'gāyatrī',
        'source': 'sacred-texts',
        'notes': 'THE GAYATRI MANTRA - Most famous Vedic verse!',
    },
    # ==========================================================================
    # MANDALA 10 - MIXED METERS (Famous hymns)
    # ==========================================================================
    {
        'mandala': 10,
        'hymn': 90,
        'verse': 1,
        'text': 'सहस्रशीर्षा पुरुषः सहस्राक्षः सहस्रपात् ।\nस भूमिं विश्वतो वृत्वात्यतिष्ठद्दशाङ्गुलम् ॥',
        'meter': 'anuṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Purusha Sukta verse 1 - Cosmic Man',
    },
    {
        'mandala': 10,
        'hymn': 90,
        'verse': 2,
        'text': 'पुरुष एवेदं सर्वं यद्भूतं यच्च भव्यम् ।\nउतामृतत्वस्येशानो यदन्नेनातिरोहति ॥',
        'meter': 'anuṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Purusha Sukta verse 2',
    },
    {
        'mandala': 10,
        'hymn': 129,
        'verse': 1,
        'text': 'नासदासीन्नो सदासीत्तदानीं नासीद्रजो नो व्योमा परो यत् ।\nकिमावरीवः कुह कस्य शर्मन्नम्भः किमासीद्गहनं गभीरम् ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Nasadiya Sukta - Creation Hymn (Before existence...)',
    },
    {
        'mandala': 10,
        'hymn': 129,
        'verse': 2,
        'text': 'न मृत्युरासीदमृतं न तर्हि न रात्र्या अह्न आसीत्प्रकेतः ।\nआनीदवातं स्वधया तदेकं तस्माद्धान्यन्न परः किं चनास ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Nasadiya Sukta verse 2',
    },
    {
        'mandala': 10,
        'hymn': 129,
        'verse': 7,
        'text': 'इयं विसृष्टिर्यत आबभूव यदि वा दधे यदि वा न ।\nयो अस्याध्यक्षः परमे व्योमन्त्सो अङ्ग वेद यदि वा न वेद ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Nasadiya Sukta verse 7 (final) - "Who really knows?"',
    },
    # ==========================================================================
    # MORE TRIṢṬUBH EXAMPLES (Most common Vedic meter - 42% of Rig Veda)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 35,
        'verse': 1,
        'text': 'आ कृष्णेन रजसा वर्तमानो निवेशयन्नमृतं मर्त्यं च ।\nहिरण्ययेन सविता रथेना देवो याति भुवनानि पश्यन् ॥',
        'meter': 'triṣṭubh',
        'source': 'sacred-texts',
        'notes': 'Savitri Sukta - Moving through dark space',
    },
    {
        'mandala': 1,
        'hymn': 50,
        'verse': 1,
        'text': 'उद्वयं तमसस्परि स्वः पश्यन्त उत्तरम् ।\nदेवं देवत्रा सूर्यमगन्म ज्योतिरुत्तमम् ॥',
        'meter': 'gāyatrī',  # This is actually Gāyatrī
        'source': 'sacred-texts',
        'notes': 'Surya Sukta - Rising above darkness',
    },
    # ==========================================================================
    # UṢṆIK (28 syllables = 4×7 or variants)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 8,
        'verse': 1,
        'text': 'एन्द्र सानसिं रयिं सजित्वानं सदासहम् ।\nवर्षिष्ठमूतये भर ॥',
        'meter': 'uṣṇik',  # From Anukramani - Hymn 1.8 is Uṣṇik
        'source': 'sacred-texts',
        'notes': 'Indra Sukta in Uṣṇik meter',
    },
    # ==========================================================================
    # BṚHATĪ (36 syllables = 4×9)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 38,
        'verse': 1,
        'text': 'क वः सखायो मरुतां जुजोषते समानीर्गौः कौ सूनृताः ।\nयूयं हि ष्ठा सुदानवो रुद्रियासो वसुयवो ये ददे वर्षिष्ठाम् ॥',
        'meter': 'bṛhatī',  # From Anukramani
        'source': 'sacred-texts',
        'notes': 'Maruts Sukta in Bṛhatī meter',
    },
    # ==========================================================================
    # PAṄKTI (40 syllables = 5×8)
    # ==========================================================================
    {
        'mandala': 1,
        'hymn': 81,
        'verse': 1,
        'text': 'इन्द्र मरुत्व इह पाहि सोमं यथा शार्यातमपिबः सुतस्य ।\nतव प्रणीती तव शूर शर्मन्नावावासो गृणते विरप्शिन् ॥',
        'meter': 'triṣṭubh',  # Actually Triṣṭubh from Anukramani
        'source': 'sacred-texts',
        'notes': 'Indra Sukta',
    },
]
