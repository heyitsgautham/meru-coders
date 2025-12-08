#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation Test Functions
"""

import sys
from indic_transliteration.sanscript import transliterate

###############################################################################
# Meru_Coders Identify

Meru_Coders_PATH = "./backend"
sys.path.insert(0, Meru_Coders_PATH)
import chanda


def Meru_Coders_identify(text):
    MI = chanda.Chanda(f"{Meru_Coders_PATH}/data")
    lr, vr = MI.identify_from_text(text, verse=True, fuzzy=True)
    return lr, vr


###############################################################################
# Skrutable Evaluation

SKRUTABLE_PATH = "./skrutable/"
sys.path.insert(0, SKRUTABLE_PATH)
from meter_identification import MeterIdentifier


def skrutable_identify(verse):
    MI = MeterIdentifier()
    result = MI.identify_meter(
        verse,
        from_scheme='DEV',
        resplit_option='resplit_lite',
        resplit_keep_midpoint=True
    )
    return result


###############################################################################
# Shreevatsa Identify

# SHREEVATSA_PATH = "./shreevatsa-meters/"
# sys.path.insert(0, SHREEVATSA_PATH)
# import identifier_pipeline


# def shreevatsa_identify(verse):
#     MI = identifier_pipeline.IdentifierPipeline()
#     result = MI.IdentifyFromText(verse)
#     return result


###############################################################################
