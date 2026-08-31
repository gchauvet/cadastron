"""Localise (et télécharge au besoin) le modèle Kraken servant de point de
départ au fine-tuning : McCATMuS.

McCATMuS est un modèle générique de transcription pour documents manuscrits,
imprimés et dactylographiés français du XVIe au XXIe siècle. Mesuré tel quel
sur le corpus TIMEUS (voir eval_model.py), il atteint 91,2 % de précision
caractère, contre 27,3 % pour un modèle entraîné de zéro sur ce même corpus :
c'est donc lui, et non un modèle maison, qui sert de base.

Il est distribué via le dépôt de modèles Kraken (htrmopo / Zenodo) et mis en
cache dans le répertoire de données utilisateur.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# DOI de la version concrète du modèle (le DOI parent 10.5281/zenodo.13788176
# désigne toutes les versions ; celui-ci pointe la V1 que nous utilisons).
MCCATMUS_DOI = "10.5281/zenodo.13788177"
MODEL_GLOB = "McCATMuS*.mlmodel"


def _cache_roots() -> list[Path]:
    """Emplacements possibles du cache htrmopo, selon la plateforme."""
    roots: list[Path] = []
    try:
        from platformdirs import user_data_dir

        roots.append(Path(user_data_dir("htrmopo")))
    except ImportError:
        pass
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        roots.append(Path(localappdata) / "htrmopo")
    roots.append(Path.home() / ".local" / "share" / "htrmopo")
    return roots


def find_base_model() -> Path | None:
    """Renvoie le chemin du modèle déjà en cache, ou None."""
    for root in _cache_roots():
        if not root.exists():
            continue
        for path in sorted(root.rglob(MODEL_GLOB)):
            return path
    return None


def ensure_base_model() -> Path:
    """Renvoie le chemin du modèle, en le téléchargeant s'il est absent."""
    path = find_base_model()
    if path is not None:
        return path

    print(f"Modele de base absent du cache, telechargement de {MCCATMUS_DOI}...")
    # PYTHONUTF8 : htrmopo lit son fichier iso15924.txt sans encodage explicite,
    # ce qui plante sous Windows (cp1252) sur un fichier UTF-8.
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    subprocess.run(["kraken", "get", MCCATMUS_DOI], check=True, env=env)

    path = find_base_model()
    if path is None:
        print(
            "Telechargement termine mais modele introuvable dans le cache.\n"
            "Lancez `kraken list` pour verifier, puis passez le chemin a la main.",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


if __name__ == "__main__":
    print(ensure_base_model())
