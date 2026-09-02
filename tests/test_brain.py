"""Tests des outils sur un mini cerveau isolé (fixture `tmp_brain`, voir conftest.py) —
search_brain, get_project, brain_overview, comme demandé dans le brief, plus quelques
cas limites utiles (résolution par nom, entité introuvable, dérivation du monde)."""

from __future__ import annotations

from pathlib import Path

import pytest

from brain_mcp.brain import Brain, EntityNotFoundError


# ---------------------------------------------------------------------------
# search_brain
# ---------------------------------------------------------------------------


def test_search_brain_trouve_par_stack(tmp_brain: Brain):
    resultats = tmp_brain.search_brain("supabase")
    slugs = {r["slug"] for r in resultats}
    assert "proj-b" in slugs


def test_search_brain_trouve_par_corps(tmp_brain: Brain):
    resultats = tmp_brain.search_brain("moteur nlp de démonstration")
    assert any(r["slug"] == "proj-a" for r in resultats)


def test_search_brain_insensible_a_la_casse(tmp_brain: Brain):
    assert tmp_brain.search_brain("SUPABASE") == tmp_brain.search_brain("supabase")


def test_search_brain_filtre_par_kind(tmp_brain: Brain):
    resultats = tmp_brain.search_brain("test", kind="contexte")
    assert resultats  # les deux contextes de test matchent sur "nom"
    assert all(r["type"] == "contexte" for r in resultats)


def test_search_brain_aucun_resultat(tmp_brain: Brain):
    assert tmp_brain.search_brain("xyz-ne-matche-rien-du-tout") == []


# ---------------------------------------------------------------------------
# get_project
# ---------------------------------------------------------------------------


def test_get_project_par_slug(tmp_brain: Brain):
    p = tmp_brain.get_project("proj-a")
    assert p["nom"] == "Projet Alpha"
    assert p["stack"] == ["python", "nlp"]
    assert p["portfolio_tier"] == "vitrine"


def test_get_project_par_nom_affiche(tmp_brain: Brain):
    p = tmp_brain.get_project("Projet Beta")
    assert p["slug"] == "proj-b"


def test_get_project_derive_le_monde_depuis_le_contexte(tmp_brain: Brain):
    assert tmp_brain.get_project("proj-a")["monde"] == "epitech"
    assert tmp_brain.get_project("proj-b")["monde"] == "perso"


def test_get_project_introuvable_leve_avec_candidats(tmp_brain: Brain):
    try:
        tmp_brain.get_project("proj-inconnu")
        assert False, "aurait dû lever EntityNotFoundError"
    except EntityNotFoundError as e:
        assert "proj-inconnu" in str(e)


# ---------------------------------------------------------------------------
# brain_overview
# ---------------------------------------------------------------------------


def test_brain_overview_compteurs(tmp_brain: Brain):
    ov = tmp_brain.brain_overview()
    assert ov["total_projets"] == 2
    assert ov["total_competences"] == 2
    assert ov["total_contextes"] == 2
    assert ov["projets_par_monde"] == {"epitech": 1, "perso": 1}


def test_brain_overview_projets_vitrine(tmp_brain: Brain):
    ov = tmp_brain.brain_overview()
    assert ov["projets_vitrine"] == ["Projet Alpha"]


def test_brain_overview_competences_solide_plus(tmp_brain: Brain):
    ov = tmp_brain.brain_overview()
    # skill-x est solide + validé -> incluse ; skill-y est notions + à-confirmer -> exclue
    assert ov["competences_solide_plus"] == ["skill-x"]


# ---------------------------------------------------------------------------
# get_skill / list_projects / list_skills / get_view (couverture additionnelle)
# ---------------------------------------------------------------------------


def test_get_skill_monde_derive_des_deux_projets(tmp_brain: Brain):
    s = tmp_brain.get_skill("skill-x")
    assert s["monde"] == ["epitech", "perso"]
    assert s["prouve_par"] == ["proj-a", "proj-b"]


def test_get_skill_sans_projet_dedie_a_monde_vide(tmp_brain: Brain):
    s = tmp_brain.get_skill("skill-y")
    assert s["monde"] == []


def test_list_projects_filtre_par_monde(tmp_brain: Brain):
    out = tmp_brain.list_projects(monde="perso")
    assert [p["slug"] for p in out] == ["proj-b"]


def test_list_skills_filtre_par_confidence(tmp_brain: Brain):
    out = tmp_brain.list_skills(confidence="à-confirmer")
    assert [s["slug"] for s in out] == ["skill-y"]


def test_get_view_lit_le_fichier(tmp_brain: Brain):
    assert "CV — vue de test" in tmp_brain.get_view("cv")


def test_get_view_manquante_leve_filenotfound(tmp_brain: Brain):
    try:
        tmp_brain.get_view("epitech")
        assert False, "aurait dû lever FileNotFoundError"
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Readiness `business` (Step 07B) — fixture isolée à 3 mondes (epitech/perso/
# business), indépendante de `tmp_brain` (conftest.py) et du vrai Brain. Ne
# touche jamais `~/CLAUDE-SHARED/brain/` — tout vit dans `tmp_path`.
# ---------------------------------------------------------------------------

PROJET_A_3M = """\
---
type: projet
nom: Projet Alpha
contexte: ctx-ecole
categorie: ia-data
role: solo
statut: livré
periode: 2026
stack: [python]
repo: ~/EPITECH/alpha
source: auto-déclaré
confidence: validé
portfolio_tier: vitrine
angle: "Projet epitech de test."
---

Corps du projet Alpha (epitech).
"""

PROJET_B_3M = """\
---
type: projet
nom: Projet Beta
contexte: ctx-perso
categorie: portfolio
role: solo
statut: en-cours
periode: 2026
stack: [nextjs]
repo: ~/perso/beta
source: auto-déclaré
confidence: validé
portfolio_tier: fondation
angle: "Projet perso de test."
---

Corps du projet Beta (perso).
"""

PROJET_C_BUSINESS = """\
---
type: projet
nom: Projet Gamma
contexte: ctx-business
categorie: outillage
role: solo
statut: vivant
periode: 2026
stack: [python, postgresql]
repo: ~/BUSINESS/gamma
source: machine-scan
confidence: à-confirmer
portfolio_tier: solide
angle: "Projet business de test — capteur de données fictif."
---

Corps du projet Gamma (business, fixture de test uniquement).
"""

SKILL_Z_EPITECH_BUSINESS = """\
---
type: skill
nom: skill-z
categorie: data-ml
niveau_connaissance: intermédiaire
niveau_source: machine-scan
confidence: à-confirmer
fraicheur: récent
prouve_par: [proj-a, proj-c]
relie_a: []
---

Skill Z, prouvée par Alpha (epitech) et Gamma (business).
"""

SKILL_W_TROIS_MONDES = """\
---
type: skill
nom: skill-w
categorie: qualite
niveau_connaissance: solide
niveau_source: validé-imran
confidence: validé
fraicheur: récent
prouve_par: [proj-a, proj-b, proj-c]
relie_a: []
---

Skill W, prouvée par les 3 projets (epitech + perso + business).
"""

CTX_ECOLE_3M = """\
---
type: contexte
monde: epitech
nom: École — test 3 mondes
forme: ecole
organisation: Epitech Test
periode: 2025-2028
statut: en cours
source: validé-imran
confidence: validé
---

Contexte école de test.
"""

CTX_PERSO_3M = """\
---
type: contexte
monde: perso
nom: Perso — test 3 mondes
forme: perso
organisation: —
periode: 2026
statut: en cours
source: validé-imran
confidence: validé
---

Contexte perso de test.
"""

CTX_BUSINESS = """\
---
type: contexte
monde: business
nom: Business — test (fixture uniquement, aucune entité réelle correspondante)
forme: business
organisation: —
periode: 2026
statut: en cours
source: machine-scan
confidence: à-confirmer
---

Contexte business de test — n'existe pas dans le vrai Brain (voir
specs/personal-os-v2/14-BRAIN-MIGRATION-COMPATIBILITY.md § Decision register
OPEN #4 : le choix réel reste ouvert, cette fixture ne le préjuge pas).
"""


@pytest.fixture
def tmp_brain_3_mondes(tmp_path: Path) -> Brain:
    """Mini cerveau isolé avec un projet epitech, un perso, un business — pour
    vérifier la readiness `business` sans jamais toucher au vrai Brain."""
    root = tmp_path / "brain"
    (root / "projets").mkdir(parents=True)
    (root / "competences").mkdir(parents=True)
    (root / "contextes").mkdir(parents=True)
    (root / "vues").mkdir(parents=True)

    (root / "projets" / "proj-a.md").write_text(PROJET_A_3M, encoding="utf-8")
    (root / "projets" / "proj-b.md").write_text(PROJET_B_3M, encoding="utf-8")
    (root / "projets" / "proj-c.md").write_text(PROJET_C_BUSINESS, encoding="utf-8")
    (root / "competences" / "skill-z.md").write_text(SKILL_Z_EPITECH_BUSINESS, encoding="utf-8")
    (root / "competences" / "skill-w.md").write_text(SKILL_W_TROIS_MONDES, encoding="utf-8")
    (root / "contextes" / "ctx-ecole.md").write_text(CTX_ECOLE_3M, encoding="utf-8")
    (root / "contextes" / "ctx-perso.md").write_text(CTX_PERSO_3M, encoding="utf-8")
    (root / "contextes" / "ctx-business.md").write_text(CTX_BUSINESS, encoding="utf-8")

    return Brain(brain_path=root)


def test_get_project_derive_le_monde_business(tmp_brain_3_mondes: Brain):
    assert tmp_brain_3_mondes.get_project("proj-c")["monde"] == "business"


def test_list_projects_filtre_par_monde_business(tmp_brain_3_mondes: Brain):
    out = tmp_brain_3_mondes.list_projects(monde="business")
    assert [p["slug"] for p in out] == ["proj-c"]


def test_list_projects_epitech_et_perso_toujours_ok_avec_3_mondes(tmp_brain_3_mondes: Brain):
    # Non-régression : l'introduction de business ne casse pas les filtres existants.
    assert [p["slug"] for p in tmp_brain_3_mondes.list_projects(monde="epitech")] == ["proj-a"]
    assert [p["slug"] for p in tmp_brain_3_mondes.list_projects(monde="perso")] == ["proj-b"]


def test_get_skill_monde_derive_epitech_et_business(tmp_brain_3_mondes: Brain):
    s = tmp_brain_3_mondes.get_skill("skill-z")
    assert s["monde"] == ["business", "epitech"]  # sorted()


def test_get_skill_monde_derive_des_3_mondes(tmp_brain_3_mondes: Brain):
    s = tmp_brain_3_mondes.get_skill("skill-w")
    assert s["monde"] == ["business", "epitech", "perso"]


def test_list_skills_filtre_par_monde_business(tmp_brain_3_mondes: Brain):
    out = tmp_brain_3_mondes.list_skills(monde="business")
    assert {s["slug"] for s in out} == {"skill-z", "skill-w"}


def test_brain_overview_compteurs_3_mondes(tmp_brain_3_mondes: Brain):
    ov = tmp_brain_3_mondes.brain_overview()
    assert ov["projets_par_monde"] == {"epitech": 1, "perso": 1, "business": 1}


def test_brain_overview_competences_par_monde_pas_de_mislabeling(tmp_brain_3_mondes: Brain):
    """skill-z (epitech+business) ne doit JAMAIS être comptée sous la clé
    composite historique "epitech+perso" — ce serait un mislabeling (aucun
    "perso" n'est impliqué). skill-w (les 3) doit avoir sa propre clé, dérivée
    dynamiquement, sans clé combinatoire codée en dur."""
    ov = tmp_brain_3_mondes.brain_overview()
    par_monde = ov["competences_par_monde"]

    assert par_monde.get("epitech+perso", 0) == 0, (
        f"mislabeling : skill-z (epitech+business) ne doit pas gonfler 'epitech+perso' "
        f"— reçu {par_monde}"
    )
    assert par_monde["business+epitech"] == 1  # skill-z, clé dérivée triée
    assert par_monde["business+epitech+perso"] == 1  # skill-w, clé dérivée triée
    # Aucune skill perso seule ni epitech seule dans cette fixture (ni proj-a ni
    # proj-b n'ont de skill dédiée à eux seuls) : uniquement les clés composites.
    assert set(par_monde) == {"business+epitech", "business+epitech+perso"}


def test_skills_non_dupliquees_entre_mondes(tmp_brain_3_mondes: Brain):
    """Une skill prouvée par plusieurs mondes reste UNE seule entité — aucune
    duplication `skill-business`/`skill-epitech`, aucune logique business-
    specific dans le stockage : `prouve_par` porte tous les projets, `monde`
    n'est qu'une dérivation en lecture."""
    assert tmp_brain_3_mondes.competences.keys() == {"skill-z", "skill-w"}
    assert len(tmp_brain_3_mondes.competences) == 2
    s = tmp_brain_3_mondes.get_skill("skill-z")
    assert s["prouve_par"] == ["proj-a", "proj-c"]
