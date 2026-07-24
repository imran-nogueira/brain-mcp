"""Tests des outils sur un mini cerveau isolé (fixture `tmp_brain`, voir conftest.py) —
search_brain, get_project, brain_overview, comme demandé dans le brief, plus quelques
cas limites utiles (résolution par nom, entité introuvable, dérivation du monde)."""

from __future__ import annotations

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
