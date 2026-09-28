"""Indian brands resolve to their ingredients, and interaction checks use them."""
from app.services import indian_medicines as im
from app.services.drug_interactions import DrugInteractionService


def test_search_is_prefix_and_carries_composition():
    hits = im.search("crocin", 5)
    assert hits and all(h["brand"].lower().startswith("crocin") for h in hits)
    assert "paracetamol" in hits[0]["generics"]


def test_bare_brand_resolves_to_shared_ingredient():
    assert im.resolve("Ecosprin")["generics"] == ["aspirin"]
    assert im.resolve("Glycomet")["generics"] == ["metformin"]


def test_exact_product_uses_its_composition():
    r = im.resolve("Dolo 650 Tablet")
    assert r["kind"] == "product" and r["generics"] == ["paracetamol"]


def test_ambiguous_brand_errs_towards_more_ingredients():
    r = im.resolve("Dolo")
    assert r["kind"] == "ambiguous" and {"paracetamol", "nimesulide"} <= set(r["generics"])


def test_unknown_name_passes_through():
    assert im.resolve("warfarin")["generics"] == ["warfarin"]


def test_brands_are_checked_for_interactions():
    out = DrugInteractionService().check_interactions(["Ecosprin", "warfarin", "Clopilet", "Omez"])
    pairs = {(i["drug_1"], i["drug_2"]) for i in out["interactions"]}
    assert ("Ecosprin", "warfarin") in pairs
    assert ("Clopilet", "Omez") in pairs


def test_indian_spelling_reaches_the_table():
    out = DrugInteractionService().check_interactions(["Thyronorm", "calcium carbonate"])
    assert out["interactions_found"] == 1
