"""Logique métier du cerveau d'Imran : chargement, dérivation, recherche, filtres.

Séparée du serveur MCP (`server.py`) pour rester testable sans transport MCP —
les outils exposés par `server.py` ne font qu'appeler ces fonctions et formater
la sortie en dict JSON-friendly.

Aucune écriture : ce module ne fait que lire les fichiers du cerveau.
"""

from __future__ import annotations

import os
from pathlib import Path

from .parser import Entity, load_entities

DEFAULT_BRAIN_PATH = Path.home() / "CLAUDE-SHARED" / "brain"

NIVEAUX_ORDRE = ["notions", "intermédiaire", "solide", "avancé"]


class EntityNotFoundError(Exception):
    """Levée quand une entité (skill/projet) n'est pas trouvée par nom/slug."""

    def __init__(self, nom: str, candidats: list[str] | None = None):
        self.nom = nom
        self.candidats = candidats or []
        msg = f"Aucune entité trouvée pour « {nom} »."
        if self.candidats:
            msg += f" Candidats proches : {', '.join(self.candidats)}"
        super().__init__(msg)


class Brain:
    """Vue en lecture seule du cerveau (`brain/projets`, `brain/competences`, `brain/contextes`)."""

    def __init__(self, brain_path: str | Path | None = None):
        resolved = brain_path or os.environ.get("BRAIN_PATH") or DEFAULT_BRAIN_PATH
        self.root = Path(resolved).expanduser().resolve()
        self.reload()

    def reload(self) -> None:
        """Recharge les entités depuis le disque (pas de cache persistant entre process)."""
        self.projets = load_entities(self.root / "projets")
        self.competences = load_entities(self.root / "competences")
        self.contextes = load_entities(self.root / "contextes")

    # ------------------------------------------------------------------
    # Dérivation du "monde" (epitech / perso) — même logique que _generer_vues.py
    # ------------------------------------------------------------------

    def projet_monde(self, slug: str) -> str:
        """Monde d'un projet, dérivé de son `contexte` (contexte -> champ `monde`)."""
        p = self.projets.get(slug)
        if p is None:
            return "?"
        ctx = self.contextes.get(str(p.get("contexte", "")))
        return str(ctx.get("monde", "?")) if ctx is not None else "?"

    def skill_mondes(self, slug: str) -> list[str]:
        """Monde(s) d'une compétence, dérivés des projets qui la prouvent (`prouve_par`)."""
        s = self.competences.get(slug)
        if s is None:
            return []
        mondes = {
            self.projet_monde(p)
            for p in s.get_list("prouve_par")
            if p in self.projets
        }
        mondes.discard("?")
        return sorted(mondes)

    # ------------------------------------------------------------------
    # Résolution nom/slug -> Entity (recherche exacte puis tolérante)
    # ------------------------------------------------------------------

    def _resolve(self, store: dict[str, Entity], nom: str) -> Entity:
        if nom in store:
            return store[nom]
        needle = nom.strip().casefold()
        for e in store.values():
            if str(e.get("nom", "")).strip().casefold() == needle:
                return e
        partiels = [
            e.slug
            for e in store.values()
            if needle in e.slug.casefold() or needle in str(e.get("nom", "")).casefold()
        ]
        raise EntityNotFoundError(nom, sorted(set(partiels))[:10])

    # ------------------------------------------------------------------
    # Outils
    # ------------------------------------------------------------------

    def search_brain(self, query: str, kind: str | None = None) -> list[dict]:
        """Cherche `query` (insensible à la casse) dans nom, categorie, stack, angle, corps."""
        needle = query.strip().casefold()
        stores: list[tuple[str, dict[str, Entity]]] = [
            ("projet", self.projets),
            ("skill", self.competences),
            ("contexte", self.contextes),
        ]
        if kind:
            stores = [(t, s) for t, s in stores if t == kind]

        resultats = []
        for type_, store in stores:
            for e in store.values():
                champs = [
                    str(e.get("nom", "")),
                    str(e.get("categorie", "")),
                    " ".join(e.get_list("stack")),
                    str(e.get("angle", "")),
                    e.corps,
                ]
                if any(needle in champ.casefold() for champ in champs):
                    resultats.append(self._brief(type_, e))
        resultats.sort(key=lambda r: (r["type"], r["slug"]))
        return resultats

    def _brief(self, type_: str, e: Entity) -> dict:
        """Champs clés d'une entité, format compact pour les résultats de recherche."""
        base = {"type": type_, "slug": e.slug, "nom": e.get("nom", e.slug)}
        if type_ == "projet":
            base.update(
                categorie=e.get("categorie"),
                statut=e.get("statut"),
                portfolio_tier=e.get("portfolio_tier"),
                angle=e.get("angle"),
                monde=self.projet_monde(e.slug),
            )
        elif type_ == "skill":
            base.update(
                categorie=e.get("categorie"),
                niveau_connaissance=e.get("niveau_connaissance"),
                confidence=e.get("confidence"),
                monde=self.skill_mondes(e.slug),
            )
        else:  # contexte
            base.update(monde=e.get("monde"), forme=e.get("forme"), statut=e.get("statut"))
        return base

    def get_skill(self, nom: str) -> dict:
        """niveau_connaissance, confidence, catégorie, prouve_par, relie_a, monde(s) dérivé(s)."""
        e = self._resolve(self.competences, nom)
        return {
            "slug": e.slug,
            "nom": e.get("nom", e.slug),
            "categorie": e.get("categorie"),
            "niveau_connaissance": e.get("niveau_connaissance"),
            "niveau_source": e.get("niveau_source"),
            "confidence": e.get("confidence"),
            "fraicheur": e.get("fraicheur"),
            "prouve_par": e.get_list("prouve_par"),
            "relie_a": e.get_list("relie_a"),
            "monde": self.skill_mondes(e.slug),
        }

    def get_project(self, nom: str) -> dict:
        """contexte, monde, portfolio_tier, angle, stack, statut, période, repo."""
        e = self._resolve(self.projets, nom)
        return {
            "slug": e.slug,
            "nom": e.get("nom", e.slug),
            "contexte": e.get("contexte"),
            "monde": self.projet_monde(e.slug),
            "categorie": e.get("categorie"),
            "role": e.get("role"),
            "statut": e.get("statut"),
            "periode": e.get("periode"),
            "portfolio_tier": e.get("portfolio_tier"),
            "angle": e.get("angle"),
            "stack": e.get_list("stack"),
            "repo": e.get("repo"),
        }

    def list_projects(
        self,
        monde: str | None = None,
        tier: str | None = None,
        contexte: str | None = None,
    ) -> list[dict]:
        """Liste filtrée (nom + tier + angle), + slug/monde pour enchaîner sur get_project."""
        out = []
        for e in self.projets.values():
            if monde and self.projet_monde(e.slug) != monde:
                continue
            if tier and e.get("portfolio_tier") != tier:
                continue
            if contexte and e.get("contexte") != contexte:
                continue
            out.append(
                {
                    "slug": e.slug,
                    "nom": e.get("nom", e.slug),
                    "portfolio_tier": e.get("portfolio_tier"),
                    "angle": e.get("angle"),
                    "monde": self.projet_monde(e.slug),
                }
            )
        out.sort(key=lambda r: (r["monde"], r["portfolio_tier"] or "", r["nom"]))
        return out

    def list_skills(
        self,
        categorie: str | None = None,
        niveau: str | None = None,
        confidence: str | None = None,
        monde: str | None = None,
    ) -> list[dict]:
        """Liste filtrée des compétences."""
        out = []
        for e in self.competences.values():
            if categorie and e.get("categorie") != categorie:
                continue
            if niveau and e.get("niveau_connaissance") != niveau:
                continue
            if confidence and e.get("confidence") != confidence:
                continue
            mondes = self.skill_mondes(e.slug)
            if monde and monde not in mondes:
                continue
            out.append(
                {
                    "slug": e.slug,
                    "nom": e.get("nom", e.slug),
                    "categorie": e.get("categorie"),
                    "niveau_connaissance": e.get("niveau_connaissance"),
                    "confidence": e.get("confidence"),
                    "monde": mondes,
                }
            )
        out.sort(key=lambda r: (r["categorie"] or "", r["nom"]))
        return out

    def get_view(self, name: str) -> str:
        """Renvoie le markdown brut d'une vue générée : cv | competences | epitech | perso."""
        mapping = {
            "cv": self.root / "vues" / "cv.md",
            "perso": self.root / "vues" / "perso-business.md",
            "competences": self.root.parent / "glossary" / "competences.md",
            "epitech": self.root.parent / "glossary" / "epitech.md",
        }
        path = mapping.get(name)
        if path is None:
            raise ValueError(
                f"Vue inconnue « {name} ». Valeurs possibles : {', '.join(mapping)}."
            )
        if not path.is_file():
            raise FileNotFoundError(
                f"Vue « {name} » absente ({path}). "
                "Régénère les vues avec `brain/_generer_vues.py`."
            )
        return path.read_text(encoding="utf-8")

    def brain_overview(self) -> dict:
        """Résumé express : compteurs par monde, projets vitrine, compétences solide+."""
        n_projets_par_monde: dict[str, int] = {}
        for e in self.projets.values():
            m = self.projet_monde(e.slug)
            n_projets_par_monde[m] = n_projets_par_monde.get(m, 0) + 1

        # Clé dérivée dynamiquement (mondes déjà triés par skill_mondes()) plutôt que
        # des combinaisons codées en dur ("epitech+perso") — reste correct quel que
        # soit le nombre de mondes actifs, sans clé à ajouter à la main pour chaque
        # nouvelle combinaison (cf. specs/personal-os-v2/14-BRAIN-MIGRATION-
        # COMPATIBILITY.md § BRAIN-MCP : l'ancienne clé "epitech+perso" en dur
        # mal-étiquetait toute skill multi-mondes, y compris epitech+business).
        n_skills_par_monde: dict[str, int] = {}
        for e in self.competences.values():
            mondes = self.skill_mondes(e.slug)
            cle = "+".join(mondes) if mondes else "?"
            n_skills_par_monde[cle] = n_skills_par_monde.get(cle, 0) + 1

        projets_vitrine = sorted(
            e.get("nom", e.slug)
            for e in self.projets.values()
            if e.get("portfolio_tier") == "vitrine"
        )
        skills_solides = sorted(
            e.get("nom", e.slug)
            for e in self.competences.values()
            if e.get("niveau_connaissance") in ("solide", "avancé")
            and e.get("confidence") == "validé"
        )

        return {
            "total_projets": len(self.projets),
            "total_competences": len(self.competences),
            "total_contextes": len(self.contextes),
            "projets_par_monde": n_projets_par_monde,
            "competences_par_monde": n_skills_par_monde,
            "projets_vitrine": projets_vitrine,
            "competences_solide_plus": skills_solides,
        }
