import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from domain.models import Draft, Place, Postcard, Weather
from domain.selection import TONES, choose_place, choose_tone
from domain.sensations import describe, time_of_day
from domain.validation import review
from infrastructure.places_catalog import load

PARAMO = Weather(temperature=-6.5, humidity=86, wind=12.7,
                 description="cubierto", code=3, is_daytime=True)
JUNGLE = Weather(temperature=28.8, humidity=81, wind=9.0,
                 description="llovizna", code=51, is_daytime=True)
BANOS = Place(name="Banos de Agua Santa", province="Tungurahua",
              lat=-1.4, lon=-78.4, soul="valle entre cascadas")


def text_of(words):
    return " ".join(["palabra"] * words)


def fake_postcard(place, tone):
    return Postcard(id="x", epoch=0, place=place, province="p", title="t", text="x",
                    tone=tone, weather=PARAMO, generated_at="", trigger="", model="")


def test_the_freezing_paramo_is_felt_in_the_body():
    described = describe(PARAMO)
    assert "entumece" in described
    assert "hasta los huesos" in described


def test_humid_heat_makes_you_sweat():
    assert "Se suda sin moverse" in describe(JUNGLE)


def test_no_number_ever_reaches_the_model():
    assert not any(c.isdigit() for c in describe(PARAMO) + describe(JUNGLE))


def test_night_overrides_the_hour():
    assert time_of_day(datetime(2026, 8, 22, 10), is_daytime=False) == "de noche"
    assert time_of_day(datetime(2026, 8, 22, 10), is_daytime=True) == "por la manana"
    assert time_of_day(datetime(2026, 8, 22, 20), is_daytime=True) == "al anochecer"


def test_a_correct_draft_passes():
    assert review(Draft("Nadie levanta la vista", text_of(100)), BANOS, "melancolico") == []


def test_rejects_digits():
    assert "contains digits" in review(Draft("Titulo limpio", text_of(99) + " 25"), BANOS, "seco")


def test_rejects_brochure_words():
    failures = review(Draft("Titulo limpio", " ".join(["magico"] * 100)), BANOS, "seco")
    assert any("banned words" in f for f in failures)


def test_rejects_the_full_place_name_in_the_title():
    failures = review(Draft("Banos de Agua Santa amanece", text_of(100)), BANOS, "seco")
    assert "the title names the place" in failures


def test_a_partial_mention_of_the_place_slips_through():
    """Known limit: the rule compares the full name, not its words."""
    failures = review(Draft("Banos bajo la niebla", text_of(100)), BANOS, "seco")
    assert "the title names the place" not in failures


def test_rejects_the_province_in_the_title():
    failures = review(Draft("Tungurahua despierta", text_of(100)), BANOS, "seco")
    assert "the title names the place" in failures


def test_rejects_a_title_that_gives_the_tone_away():
    draft = Draft("Un aire melancolico", text_of(100))
    failures = review(draft, BANOS, "melancolico y contenido")
    assert any("copies the tone" in f for f in failures)


def test_rejects_texts_outside_the_measure():
    assert any("length" in f for f in review(Draft("Titulo", "muy corto"), BANOS, "seco"))


def test_an_empty_text_short_circuits_the_review():
    assert review(Draft("Titulo", ""), BANOS, "seco") == ["empty postcard"]


def test_the_catalog_is_made_of_domain_models():
    catalog = load()
    assert len(catalog) == 50
    assert all(isinstance(place, Place) for place in catalog)


def test_it_never_returns_to_a_recent_place():
    catalog = load()
    memory = [fake_postcard(place.name, TONES[0]) for place in catalog[:18]]
    chosen = {choose_place(memory, catalog).name for _ in range(60)}
    assert not chosen & {postcard.place for postcard in memory}


def test_it_never_repeats_the_latest_tones():
    memory = [fake_postcard("x", tone) for tone in TONES[:8]]
    assert {choose_tone(memory) for _ in range(60)}.isdisjoint(set(TONES[:8]))


def test_with_the_whole_country_visited_it_starts_over():
    catalog = load()
    memory = [fake_postcard(place.name, "t") for place in catalog]
    assert choose_place(memory, catalog) in catalog
