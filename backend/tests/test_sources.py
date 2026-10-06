from app.sources import normalize_search_text
from app.sources import exact_reference


def test_arabic_normalization_removes_diacritics_and_alif_variants():
    value="\u0625\u0650\u0646\u0651\u064e\u0645\u064e\u0627 \u0625\u0650\u0644\u064e\u0649"
    assert normalize_search_text(value) == "\u0627\u0646\u0645\u0627 \u0627\u0644\u064a"


def test_arabic_normalization_preserves_non_alif_hamza_letters_in_text_norm():
    value="\u0627\u0644\u0645\u064f\u0624\u0652\u0645\u0650\u0646\u0650\u064a\u0646\u064e"
    assert normalize_search_text(value) == "\u0627\u0644\u0645\u0624\u0645\u0646\u064a\u0646"


def test_explicit_quran_coordinates_and_arabic_digits_are_recognized():
    assert exact_reference('Quran 96:1')==(96,1)
    assert exact_reference('سورة العلق ٩٦:١')==(96,1)


def test_hadith_reference_is_not_silently_remapped_between_local_numbers():
    assert exact_reference('Sahih Muslim 160')==('muslim','160')
    assert exact_reference('muslim:403')==('muslim','403')
