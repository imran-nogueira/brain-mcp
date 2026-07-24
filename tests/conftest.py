"""Fixtures pytest : un mini cerveau isolé (indépendant du vrai `~/CLAUDE-SHARED/brain/`
pour que les tests restent stables même si Imran édite ses entités)."""

from __future__ import annotations

from pathlib import Path

import pytest

from brain_mcp.brain import Brain

PROJET_A = """\
---
type: projet
nom: Projet Alpha
contexte: ctx-ecole
categorie: ia-data
role: solo
statut: livré
periode: 2026
stack: [python, nlp]
repo: ~/EPITECH/alpha
source: auto-déclaré
confidence: validé
portfolio_tier: vitrine
angle: "Un projet de démo, avec une virgule, dans l'angle."
---

Corps du projet Alpha : un moteur NLP de démonstration.

**Contexte :** [[ctx-ecole]]
"""

PROJET_B = """\
---
type: projet
nom: Projet Beta
contexte: ctx-perso
categorie: portfolio
role: solo
statut: en-cours
periode: 2026
stack: [nextjs, supabase]
repo: ~/perso/beta
source: auto-déclaré
confidence: validé
portfolio_tier: fondation
angle: "Un side-project perso avec Supabase."
---

Corps du projet Beta : side-project perso.
"""

SKILL_X = """\
---
type: skill
nom: skill-x
categorie: data-ml
niveau_connaissance: solide
niveau_source: validé-imran
confidence: validé
fraicheur: récent
prouve_par: [proj-a, proj-b]
relie_a: []
---

Skill X, prouvée par Alpha et Beta.
"""

SKILL_Y = """\
---
type: skill
nom: skill-y
categorie: devops
niveau_connaissance: notions
niveau_source: machine-scan
confidence: à-confirmer
fraicheur: inconnue
prouve_par: []
relie_a: []
---

Skill Y, sans projet dédié (environnement).
"""

CTX_ECOLE = """\
---
type: contexte
monde: epitech
nom: École — test
forme: ecole
organisation: Epitech Test
periode: 2025-2028
statut: en cours
source: validé-imran
confidence: validé
---

Contexte école de test.
"""

CTX_PERSO = """\
---
type: contexte
monde: perso
nom: Perso — test
forme: perso
organisation: —
periode: 2026
statut: en cours
source: validé-imran
confidence: validé
---

Contexte perso de test.
"""

VUE_CV = "# CV — vue de test\n\nContenu factice.\n"


@pytest.fixture
def tmp_brain(tmp_path: Path) -> Brain:
    root = tmp_path / "brain"
    (root / "projets").mkdir(parents=True)
    (root / "competences").mkdir(parents=True)
    (root / "contextes").mkdir(parents=True)
    (root / "vues").mkdir(parents=True)
    (root.parent / "glossary").mkdir(parents=True)

    (root / "projets" / "proj-a.md").write_text(PROJET_A, encoding="utf-8")
    (root / "projets" / "proj-b.md").write_text(PROJET_B, encoding="utf-8")
    (root / "competences" / "skill-x.md").write_text(SKILL_X, encoding="utf-8")
    (root / "competences" / "skill-y.md").write_text(SKILL_Y, encoding="utf-8")
    (root / "contextes" / "ctx-ecole.md").write_text(CTX_ECOLE, encoding="utf-8")
    (root / "contextes" / "ctx-perso.md").write_text(CTX_PERSO, encoding="utf-8")
    (root / "vues" / "cv.md").write_text(VUE_CV, encoding="utf-8")

    return Brain(brain_path=root)
