"""
Export ready-to-paste payloads for manual Copilot testing.
==========================================================
Run this to get payloads you can copy-paste into Copilot right now.
No API key or browser automation needed.

Run: python examples/export_manual_payloads.py
"""

from laaf.generators.payload_generator import PayloadGenerator
from laaf.taxonomy.base import Category

# Generate best payloads per category (most effective for Copilot per paper)
CATEGORIES_TO_TEST = [
    (Category.SEMANTIC,   "Semantic — highest bypass on well-defended platforms"),
    (Category.LAYERED,    "Layered — multiplicative detection failure"),
    (Category.ENCODING,   "Encoding — scanner-model asymmetry"),
    (Category.STRUCTURAL, "Structural — document infrastructure disguise"),
    (Category.TRIGGER,    "Trigger — conditional activation"),
]

print("=" * 70)
print("LAAF — Manual Copilot Test Payloads")
print("Copy-paste each payload into your Copilot chat.")
print("Record: EXECUTED / BLOCKED / WARNING + the response you get.")
print("=" * 70)

gen = PayloadGenerator(seed=2026)

for category, desc in CATEGORIES_TO_TEST:
    payloads = gen.generate(count=3, technique_ids=None)
    # Filter to this category
    cat_payloads = [p for p in gen.generate(count=30) if p.category == category.value][:3]

    print(f"\n{'─'*70}")
    print(f"CATEGORY: {category.value.upper()} — {desc}")
    print(f"{'─'*70}")

    for i, p in enumerate(cat_payloads, 1):
        print(f"\n[{p.technique_id}] {p.technique_name}")
        print(f"Attack Vector: {p.attack_vector}")
        print(f"{'·'*50}")
        print(p.content)
        print(f"{'·'*50}")
        print(f"→ Record outcome: [ ] EXECUTED  [ ] BLOCKED  [ ] WARNING")
        print(f"→ Response notes: ___________________________________________")

print("\n" + "=" * 70)
print("After testing, note which technique IDs caused EXECUTED outcomes.")
print("Then run: laaf scan --target mock --dry-run  to generate more variants")
print("Reference: arXiv:2507.10457 — Table 4 for expected bypass rates")
