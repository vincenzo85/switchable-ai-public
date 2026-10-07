"""Chunking e anonimizzazione (core/domain/text.py)."""
from core.domain.text import approx_tokens, chunk_markdown, scrub_pii


def test_heading_stays_with_its_body():
    doc = ("# Runbook\n\n" + "Introduzione lunga. " * 30 + "\n\n## L'indice RAG è vuoto\n\n"
           "Lanciare `./run.sh rag-build`.\n\n## Altro\n\n" + "Testo. " * 20)
    chunks = chunk_markdown(doc, 300)
    target = [c for c in chunks if "L'indice RAG è vuoto" in c]
    assert target and "rag-build" in target[0]


def test_sections_are_not_merged_across_headings():
    doc = "## A\n\nuno\n\n## B\n\ndue"
    assert chunk_markdown(doc, 800) == ["## A\n\nuno", "## B\n\ndue"]


def test_long_section_is_split_but_keeps_heading_as_context():
    doc = "## Sezione lunga\n\n" + "\n\n".join(f"Paragrafo {i} " + "x" * 200 for i in range(6))
    chunks = chunk_markdown(doc, 500)
    assert len(chunks) > 1
    assert all(c.startswith("## Sezione lunga") for c in chunks)


def test_plain_text_without_headings_still_chunks():
    assert chunk_markdown("a\n\nb", 800) == ["a\n\nb"]


def test_scrub_pii_replaces_email_iban_cf_phone():
    t, n = scrub_pii("Scrivi a anna@example.com, IBAN IT60X0542811101000000123456, "
                     "CF RSSMRA80A01H501U, tel +39 333 1234567")
    assert "@" not in t and "IT60X" not in t and "RSSMRA" not in t and "1234567" not in t
    assert n == 4


def test_approx_tokens():
    assert approx_tokens("") == 0 and approx_tokens("abcd" * 10) == 10
