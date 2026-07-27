# brain-mcp

Serveur MCP **lecture seule** qui expose le cerveau d'Imran (`~/CLAUDE-SHARED/brain/`) à
n'importe quel client Claude (Claude Code, Cowork, Chrome). « Tu es une partie de mon
cerveau » rendu littéral.

- **FastMCP (Python)**, transport **stdio**, **local**.
- **Lecture seule** : aucun outil n'écrit dans le cerveau. La validation/écriture viendra
  plus tard avec la porte de validation (voir `brain/SCHEMA.md`).
- **Pas d'embeddings, pas de base vectorielle** : le cerveau fait ~46 Ko / 58 fichiers,
  une recherche structurée + mots-clés suffit très largement. Des embeddings seraient de
  l'over-engineering pour ce volume.
- Chemin du cerveau **configurable** via la variable d'env `BRAIN_PATH`
  (défaut : `~/CLAUDE-SHARED/brain`).

Brief d'origine : `~/CLAUDE-CODE-SYSTEM/inbox-from-cowork/2026-07-18-instruction-brain-mcp-serveur-phase3.md`.

## Outils exposés

| Outil | Description |
|---|---|
| `search_brain(query, kind?)` | Cherche un mot-clé (nom, catégorie, stack, angle, corps) dans projets/compétences/contextes. |
| `get_skill(nom)` | Détail d'une compétence : niveau, confiance, catégorie, `prouve_par`, `relie_a`, monde(s) dérivé(s). |
| `get_project(nom)` | Détail d'un projet : contexte, monde, tier portfolio, angle, stack, statut, période, repo. |
| `list_projects(monde?, tier?, contexte?)` | Liste filtrée de projets. |
| `list_skills(categorie?, niveau?, confidence?, monde?)` | Liste filtrée de compétences. |
| `get_view(name)` | Markdown brut d'une vue générée : `cv` \| `competences` \| `epitech` \| `perso`. |
| `brain_overview()` | Résumé express : compteurs par monde, projets vitrine, compétences solide+. |

Chaque outil a une docstring FR détaillée (schéma de retour, exemples) — visible depuis
n'importe quel client MCP.

## Installation

```bash
cd ~/BRAIN-MCP
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Lancer le serveur

```bash
# via le script installé par pyproject.toml
~/BRAIN-MCP/.venv/bin/brain-mcp

# ou directement
~/BRAIN-MCP/.venv/bin/python -m brain_mcp.server

# avec un chemin de cerveau custom
BRAIN_PATH=~/autre-cerveau ~/BRAIN-MCP/.venv/bin/brain-mcp
```

Le serveur parle stdio — il ne fait rien d'intéressant lancé seul dans un terminal
(il attend des messages JSON-RPC sur stdin). C'est normal.

Pour explorer les outils interactivement, utilise le MCP Inspector :

```bash
npx @modelcontextprotocol/inspector ~/BRAIN-MCP/.venv/bin/brain-mcp
```

## Tests

```bash
cd ~/BRAIN-MCP
.venv/bin/python -m pytest -v
```

- `tests/test_parser.py` : parseur testé sur une **entité réelle** du cerveau
  (`brain/projets/agentos-v2.md`) — skippé proprement si lancé sur une machine sans
  le cerveau monté.
- `tests/test_brain.py` : `search_brain`, `get_project`, `brain_overview` (+ couverture
  additionnelle) sur un mini cerveau isolé et déterministe (fixture `tmp_brain`).

## Enregistrer le serveur dans un client — ⚠️ à exécuter toi-même

> Cette étape modifie la config d'un client Claude → validation Imran requise
> (règle stricte CLAUDE.md n°4 / porte STOP du brief). Le serveur ne s'auto-enregistre
> **nulle part** — copie-colle et lance la commande qui te convient.

### Claude Code

```bash
claude mcp add brain -s user -e BRAIN_PATH="$HOME/CLAUDE-SHARED/brain" \
  -- "$HOME/BRAIN-MCP/.venv/bin/brain-mcp"
```

- `-s user` : dispo dans toutes tes sessions Claude Code (pas juste le projet courant).
  Utilise `-s local` pour ne l'activer que dans le dossier courant.
- Vérifier : `claude mcp list` puis `claude mcp get brain`.
- Retirer : `claude mcp remove brain`.

### Cowork

Cowork lit une config MCP au format JSON standard (`mcpServers`). Ajoute une entrée
équivalente à celle-ci dans la config MCP de Cowork (emplacement selon ta version de
Cowork — cherche le fichier qui contient déjà tes autres serveurs MCP, ex. Supabase,
Gmail) :

```json
{
  "mcpServers": {
    "brain": {
      "command": "/Users/imran/BRAIN-MCP/.venv/bin/brain-mcp",
      "env": {
        "BRAIN_PATH": "/Users/imran/CLAUDE-SHARED/brain"
      }
    }
  }
}
```

### Claude en Chrome

Le même JSON `mcpServers` ci-dessus s'applique généralement à tout client basé sur le
SDK MCP standard — vérifie l'emplacement exact de la config dans les réglages MCP de
l'extension Chrome avant d'y toucher.

## Structure

```
BRAIN-MCP/
├── pyproject.toml
├── README.md
├── src/brain_mcp/
│   ├── parser.py   # frontmatter YAML naïf + corps markdown (même logique que _generer_vues.py)
│   ├── brain.py     # chargement, dérivation du monde, recherche, filtres (testable sans MCP)
│   └── server.py    # FastMCP : 7 outils, modèles Pydantic, stdio
└── tests/
    ├── conftest.py
    ├── test_parser.py
    └── test_brain.py
```

## Limites connues (v1)

- Recherche par mots-clés exacts (sous-chaîne, insensible à la casse) — pas de recherche
  floue/sémantique. Suffisant vu le volume ; à revoir si le cerveau grossit beaucoup.
- Pas d'écriture, pas de validation d'entité — lecture seule assumée.
- Le serveur relit le disque à chaque appel d'outil (coût négligeable vu la taille du
  cerveau) : toute édition d'entité par Imran est visible immédiatement, sans redémarrer
  le serveur.
