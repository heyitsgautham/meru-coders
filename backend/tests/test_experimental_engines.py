"""The experimental engines still load and identify after moving out of backend/core."""

import pytest

from backend.config import settings
from backend.experimental.enhanced_chanda import EnhancedChanda
from backend.experimental.enhanced_chanda_identify import EnhancedIdentifyMixin

MANDAKRANTA = "श्यामास्वाङ्गं चकितहरिणीप्रेक्षणे दृष्टिपातं"


@pytest.fixture(scope="module")
def enhanced():
    return EnhancedChanda(str(settings.DATA_DIR))


def test_enhanced_engine_combines_its_mixins():
    assert issubclass(EnhancedChanda, EnhancedIdentifyMixin)


def test_enhanced_engine_identifies_a_mandakranta_line(enhanced):
    result = enhanced.identify_line(MANDAKRANTA)
    assert result["found"]
    assert result["chanda"][0][0] == "Mandākrāntā"


def test_enhanced_engine_reports_every_line(enhanced):
    result = enhanced.identify_from_text(f"{MANDAKRANTA}\nवागर्थाविव सम्पृक्तौ")
    assert len(result["result"]["line"]) == 2


def test_modal_and_hybrid_engines_import():
    from backend.experimental import chanda_hybrid, chanda_modal

    assert chanda_modal.ChandaModal.__mro__[1].__name__ == "Chanda"
    assert chanda_hybrid.ChandaHybrid.__mro__[1].__name__ == "Chanda"
