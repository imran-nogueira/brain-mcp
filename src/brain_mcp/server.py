#!/usr/bin/env python3
"""Serveur MCP « cerveau d'Imran » — lecture seule, stdio, sans embeddings.

Expose en lecture seule le registre canonique `~/CLAUDE-SHARED/brain/` (entités
markdown + frontmatter YAML) à n'importe quel client MCP (Claude Code, Cowork,
Chrome). Recherche structurée + mots-clés — pas d'embeddings ni de base
vectorielle, le cerveau est trop petit (~46 Ko / 58 fichiers) pour le justifier.

Chemin du cerveau configurable via la variable d'env `BRAIN_PATH`
(défaut : `~/CLAUDE-SHARED/brain`).
"""

from __future__ import annotations

from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from .brain import Brain, EntityNotFoundError

mcp = FastMCP("brain_mcp")

# Une seule instance ; `reload()` relit le disque à chaque appel d'outil (le
# cerveau est petit, le coût est négligeable, et ça évite de servir des
# données périmées si Imran édite une entité pendant que le serveur tourne).
_brain = Brain()


def _fresh() -> Brain:
    _brain.reload()
    return _brain


# ----------------------------------------------------------------------
# Modèles d'entrée
# ----------------------------------------------------------------------


class SearchBrainInput(BaseModel):
    """Entrée pour la recherche dans le cerveau."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="Terme recherché (insensible à la casse), ex. 'supabase', 'nlp', 'stage'.",
        min_length=1,
        max_length=200,
    )
    kind: Optional[Literal["skill", "projet", "contexte"]] = Field(
        default=None,
        description="Filtre optionnel par type d'entité. Par défaut : cherche dans les trois.",
    )


class GetSkillInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nom: str = Field(
        ...,
        description="Nom ou slug de la compétence, ex. 'supabase', 'api-llm'.",
        min_length=1,
        max_length=200,
    )


class GetProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nom: str = Field(
        ...,
        description="Nom ou slug du projet, ex. 'agentos-v2', 'Bookworm (ALICE)'.",
        min_length=1,
        max_length=200,
    )


class ListProjectsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    monde: Optional[Literal["epitech", "perso"]] = Field(
        default=None, description="Filtre par monde : 'epitech' (école/stage) ou 'perso'."
    )
    tier: Optional[Literal["vitrine", "solide", "fondation"]] = Field(
        default=None, description="Filtre par valeur portfolio."
    )
    contexte: Optional[str] = Field(
        default=None,
        description="Filtre par slug de contexte exact, ex. 'ecole-epitech', 'stage-gs-group'.",
    )


class ListSkillsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    categorie: Optional[str] = Field(
        default=None, description="Filtre par catégorie, ex. 'ia-llm', 'langage', 'devops'."
    )
    niveau: Optional[Literal["notions", "intermédiaire", "solide", "avancé"]] = Field(
        default=None, description="Filtre par niveau de connaissance."
    )
    confidence: Optional[Literal["inféré", "à-confirmer", "validé"]] = Field(
        default=None, description="Filtre par niveau de confiance de la donnée."
    )
    monde: Optional[Literal["epitech", "perso"]] = Field(
        default=None, description="Filtre par monde où la compétence est prouvée."
    )


class GetViewInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: Literal["cv", "competences", "epitech", "perso"] = Field(
        ..., description="Vue générée à récupérer : cv, competences, epitech ou perso."
    )


# ----------------------------------------------------------------------
# Outils
# ----------------------------------------------------------------------

_RO = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


@mcp.tool(
    name="search_brain",
    annotations={"title": "Chercher dans le cerveau", **_RO},
)
def search_brain(params: SearchBrainInput) -> list[dict]:
    """Cherche un mot-clé dans le cerveau d'Imran (projets, compétences, contextes).

    Cherche `query` (insensible à la casse) dans le nom, la catégorie, le stack,
    l'angle et le corps markdown de chaque entité. Ne modifie rien (lecture seule).

    Args:
        params (SearchBrainInput): query (str) + kind optionnel ("skill"|"projet"|"contexte").

    Returns:
        list[dict]: une entrée par entité trouvée, avec des champs clés qui
        varient selon le type (projet : categorie/statut/portfolio_tier/angle/monde ;
        skill : categorie/niveau_connaissance/confidence/monde ;
        contexte : monde/forme/statut). Liste vide si rien ne correspond.

    Examples:
        - "Quels projets utilisent Supabase ?" -> query="supabase", kind="projet"
        - "Qu'est-ce qui touche au NLP dans le cerveau ?" -> query="nlp"
    """
    return _fresh().search_brain(params.query, params.kind)


@mcp.tool(
    name="get_skill",
    annotations={"title": "Détail d'une compétence", **_RO},
)
def get_skill(params: GetSkillInput) -> dict:
    """Renvoie le détail d'une compétence par nom ou slug.

    Args:
        params (GetSkillInput): nom (str) — nom ou slug de la compétence.

    Returns:
        dict: {slug, nom, categorie, niveau_connaissance, niveau_source,
        confidence, fraicheur, prouve_par (list[str]), relie_a (list[str]),
        monde (list[str], dérivé des projets qui prouvent la compétence)}.
        {"error": "..."} si la compétence n'est pas trouvée (avec des
        candidats proches quand c'est possible).

    Examples:
        - "Qu'est-ce qu'Imran connaît en Supabase ?" -> nom="supabase"
        - Don't use when: tu cherches un projet (utilise get_project).
    """
    try:
        return _fresh().get_skill(params.nom)
    except EntityNotFoundError as e:
        return {"error": str(e)}


@mcp.tool(
    name="get_project",
    annotations={"title": "Détail d'un projet", **_RO},
)
def get_project(params: GetProjectInput) -> dict:
    """Renvoie le détail d'un projet par nom ou slug.

    Args:
        params (GetProjectInput): nom (str) — nom ou slug du projet.

    Returns:
        dict: {slug, nom, contexte, monde, categorie, role, statut, periode,
        portfolio_tier, angle, stack (list[str]), repo}.
        {"error": "..."} si le projet n'est pas trouvé (avec des candidats
        proches quand c'est possible).

    Examples:
        - "Raconte-moi le projet AgentOS" -> nom="agentos-v2"
        - Don't use when: tu cherches une compétence (utilise get_skill).
    """
    try:
        return _fresh().get_project(params.nom)
    except EntityNotFoundError as e:
        return {"error": str(e)}


@mcp.tool(
    name="list_projects",
    annotations={"title": "Lister les projets", **_RO},
)
def list_projects(params: ListProjectsInput) -> list[dict]:
    """Liste les projets, filtrable par monde, valeur portfolio et contexte.

    Args:
        params (ListProjectsInput): monde ("epitech"|"perso"), tier
            ("vitrine"|"solide"|"fondation"), contexte (slug exact) — tous
            optionnels et combinables (ET logique).

    Returns:
        list[dict]: [{slug, nom, portfolio_tier, angle, monde}, ...],
        trié par monde puis tier puis nom.

    Examples:
        - "Quels sont mes projets vitrine côté Epitech ?" -> monde="epitech", tier="vitrine"
        - "Tous les projets perso" -> monde="perso"
    """
    return _fresh().list_projects(params.monde, params.tier, params.contexte)


@mcp.tool(
    name="list_skills",
    annotations={"title": "Lister les compétences", **_RO},
)
def list_skills(params: ListSkillsInput) -> list[dict]:
    """Liste les compétences, filtrable par catégorie, niveau, confiance, monde.

    Args:
        params (ListSkillsInput): categorie, niveau, confidence, monde — tous
            optionnels et combinables (ET logique).

    Returns:
        list[dict]: [{slug, nom, categorie, niveau_connaissance, confidence,
        monde (list[str])}, ...], trié par catégorie puis nom.

    Examples:
        - "Mes compétences IA/LLM solides ?" -> categorie="ia-llm", niveau="solide"
        - "Compétences encore à confirmer ?" -> confidence="à-confirmer"
    """
    return _fresh().list_skills(params.categorie, params.niveau, params.confidence, params.monde)


@mcp.tool(
    name="get_view",
    annotations={"title": "Récupérer une vue générée", **_RO},
)
def get_view(params: GetViewInput) -> str:
    """Renvoie le markdown brut d'une vue générée du cerveau.

    Args:
        params (GetViewInput): name — "cv" (compétences validées), "competences"
            (index unifié), "epitech" (projets monde epitech rangés par tier),
            "perso" (projets monde perso rangés par tier).

    Returns:
        str: contenu markdown complet de la vue. Chaîne commençant par
        "Erreur :" si la vue est introuvable sur disque (pas encore générée).

    Examples:
        - "Montre-moi mon CV compétences" -> name="cv"
        - "Montre-moi la vue projets Epitech" -> name="epitech"
    """
    try:
        return _fresh().get_view(params.name)
    except FileNotFoundError as e:
        return f"Erreur : {e}"


@mcp.tool(
    name="brain_overview",
    annotations={"title": "Vue d'ensemble du cerveau", **_RO},
)
def brain_overview() -> dict:
    """Résumé express du cerveau — le « qui est Imran » en un appel.

    Returns:
        dict: {total_projets, total_competences, total_contextes,
        projets_par_monde (dict monde -> compte), competences_par_monde
        (dict monde -> compte), projets_vitrine (list[str] noms),
        competences_solide_plus (list[str] noms, niveau solide/avancé +
        confidence validé)}.

    Examples:
        - "Fais-moi un résumé de mon profil tech" -> aucun paramètre
    """
    return _fresh().brain_overview()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
