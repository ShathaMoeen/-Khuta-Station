from app.station_flow import _provenance_reference_matches


def test_quran_master_content_provenance_accepts_display_prefix_only_for_matching_coordinate():
    row = {"type": "quran", "reference": "96:1", "provenance_reference": "Quran 96:1", "surah": 96, "ayah": 1}
    assert _provenance_reference_matches(row)
    assert not _provenance_reference_matches({**row, "provenance_reference": "Quran 96:2"})


def test_bukhari_master_content_provenance_accepts_known_display_label_with_same_number():
    row = {"type": "hadith", "source": "quranlab/hadith:bukhari-ar", "reference": "bukhari:3",
           "provenance_reference": "Sahih al-Bukhari 3"}
    assert _provenance_reference_matches(row)
    assert not _provenance_reference_matches({**row, "provenance_reference": "Sahih al-Bukhari 4"})


def test_provenance_reference_does_not_accept_unrecognized_rewrites():
    row = {"type": "hadith", "source": "quranlab/hadith:muslim-ar", "reference": "muslim:3",
           "provenance_reference": "Sahih Muslim 3"}
    assert not _provenance_reference_matches(row)


def test_muslim_collection_number_is_not_assumed_equivalent_to_local_reference():
    row = {"type": "hadith", "source": "quranlab/hadith:muslim-ar", "reference": "muslim:403",
           "provenance_reference": "Sahih Muslim 160"}
    assert not _provenance_reference_matches(row)
