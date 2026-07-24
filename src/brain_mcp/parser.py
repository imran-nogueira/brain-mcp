"""Parseur d'entités du cerveau (frontmatter YAML naïf + corps markdown).

Réutilise la même logique que `~/CLAUDE-SHARED/brain/_generer_vues.py` (split sur `---`,
YAML naïf ligne à ligne, strip des guillemets) pour rester cohérent avec le générateur
de vues existant. Étend cette logique pour conserver aussi le corps markdown, nécessaire
à `search_brain` (qui doit chercher dans le corps, pas seulement le frontmatter).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)


@dataclass
class Entity:
    """Une entité du cerveau : un fichier markdown = une entité."""

    slug: str
    path: Path
    fields: dict[str, str | list[str]] = field(default_factory=dict)
    corps: str = ""

    def get(self, key: str, default=None):
        return self.fields.get(key, default)

    def get_list(self, key: str) -> list[str]:
        v = self.fields.get(key, [])
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v.strip():
            return [v.strip()]
        return []


def _parse_value(raw: str) -> str | list[str]:
    """Parse une valeur de frontmatter : liste `[a, b]`, chaîne entre guillemets, ou brute."""
    v = raw.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        items = []
        for x in inner.split(","):
            x = x.strip()
            if len(x) >= 2 and x[0] == x[-1] == '"':
                x = x[1:-1]
            if x:
                items.append(x)
        return items
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    return v


def parse_frontmatter(text: str) -> tuple[dict[str, str | list[str]], str]:
    """Découpe un fichier entité en (frontmatter, corps).

    Frontmatter : YAML naïf ligne par ligne (`clé: valeur`), pas de parseur YAML
    complet — cohérent avec `_generer_vues.py` puisque le cerveau reste à ~46 Ko / 58
    fichiers (pas besoin d'une dépendance YAML pour ça).
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text.strip()

    raw_fm, corps = m.group(1), m.group(2)
    d: dict[str, str | list[str]] = {}
    for line in raw_fm.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip()] = _parse_value(v)
    return d, corps.strip()


def parse_entity(path: Path) -> Entity:
    """Parse un fichier entité complet (frontmatter + corps)."""
    text = path.read_text(encoding="utf-8")
    fields_, corps = parse_frontmatter(text)
    slug = path.stem
    return Entity(slug=slug, path=path, fields=fields_, corps=corps)


def load_entities(directory: Path) -> dict[str, Entity]:
    """Charge toutes les entités `.md` d'un dossier (projets/, competences/, contextes/)."""
    if not directory.is_dir():
        return {}
    out = {}
    for p in sorted(directory.glob("*.md")):
        e = parse_entity(p)
        out[e.slug] = e
    return out
