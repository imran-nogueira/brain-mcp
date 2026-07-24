"""Tests du parseur — sur une entité RÉELLE du cerveau d'Imran, comme demandé
dans le brief (`~/CLAUDE-SHARED/brain/projets/agentos-v2.md`).

Si ce fichier n'existe pas sur la machine qui lance les tests (autre poste,
CI sans le cerveau monté), le test est proprement skippé plutôt que faux-positif.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from brain_mcp.parser import parse_entity, parse_frontmatter

REAL_ENTITY = Path.home() / "CLAUDE-SHARED" / "brain" / "projets" / "agentos-v2.md"

pytestmark = pytest.mark.skipif(
    not REAL_ENTITY.is_file(),
    reason=f"cerveau réel absent ({REAL_ENTITY}) — attendu sur la machine d'Imran",
)


def test_parse_entity_reelle_champs_scalaires():
    e = parse_entity(REAL_ENTITY)
    assert e.slug == "agentos-v2"
    assert e.get("type") == "projet"
    assert e.get("nom") == "AgentOS v2 (archivé)"
    assert e.get("contexte") == "perso"
    assert e.get("portfolio_tier") == "vitrine"


def test_parse_entity_reelle_listes():
    e = parse_entity(REAL_ENTITY)
    stack = e.get_list("stack")
    assert stack == ["n8n", "supabase", "api-llm", "nextjs"]


def test_parse_entity_reelle_angle_guillemets_conserve_les_virgules():
    e = parse_entity(REAL_ENTITY)
    angle = e.get("angle")
    assert isinstance(angle, str)
    # L'angle contient des virgules dans le texte : la valeur entre guillemets
    # ne doit pas être tronquée/éclatée comme une liste.
    assert "Vapi, Twilio, Claude, n8n, Supabase" in angle


def test_parse_entity_reelle_corps_non_vide():
    e = parse_entity(REAL_ENTITY)
    assert "Assistant vocal inbound" in e.corps
    assert "[[perso]]" in e.corps


def test_parse_frontmatter_separe_bien_frontmatter_et_corps():
    text = REAL_ENTITY.read_text(encoding="utf-8")
    fm, corps = parse_frontmatter(text)
    assert fm["type"] == "projet"
    assert not corps.startswith("---")
    assert not corps.startswith("\n")
