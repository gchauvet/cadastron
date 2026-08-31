"""Prépare le jeu d'entraînement pour le fine-tuning à partir des lignes
extraites par le pipeline (`output/lines/<page>/*.png`).

Kraken (`ketos train -f path`) attend, à côté de chaque image de ligne, un
fichier texte de même nom terminé par `.gt.txt` contenant sa transcription.
Ce script rassemble toutes les lignes de toutes les pages dans un répertoire
unique et crée les `.gt.txt` manquants (vides), prêts à être remplis à la main.

Les transcriptions déjà saisies ne sont JAMAIS écrasées : le script est
ré-exécutable sans risque après chaque nouveau passage du pipeline.

Conventions de transcription :
  - transcrire exactement ce qui est écrit, sans corriger ni développer les
    abréviations ;
  - le signe « ditto » (reprise de la valeur de la cellule au-dessus, dans la
    MÊME colonne) se note `/` ; le laisser tel quel, sa résolution se fait en
    post-traitement ;
  - laisser le `.gt.txt` vide si la ligne est illisible ou vide : elle sera
    simplement exclue de l'entraînement.

Usage:
    python training/prepare_finetune.py
    python training/prepare_finetune.py --status
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LINES_DIR = PROJECT_ROOT / "output" / "lines"
GT_DIR = Path(__file__).parent / "cadastre_gt"


def link_or_copy(src: Path, dst: Path) -> None:
    """Lien physique si possible (economise l'espace), copie sinon."""
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def collect() -> tuple[int, int]:
    """Rassemble les lignes et cree les .gt.txt manquants.

    Renvoie (nombre de lignes total, nombre de .gt.txt crees).
    """
    GT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    created = 0
    for sheet_dir in sorted(p for p in LINES_DIR.iterdir() if p.is_dir()):
        for png in sorted(sheet_dir.glob("*.png")):
            # Prefixe par la page pour eviter les collisions entre onglets.
            dst = GT_DIR / f"{sheet_dir.name}__{png.name}"
            link_or_copy(png, dst)
            gt = dst.with_suffix("").with_suffix(".gt.txt")
            if not gt.exists():
                gt.write_text("", encoding="utf-8")
                created += 1
            total += 1
    return total, created


def status() -> tuple[int, int]:
    """Renvoie (lignes transcrites, lignes totales)."""
    if not GT_DIR.exists():
        return 0, 0
    pngs = sorted(GT_DIR.glob("*.png"))
    filled = 0
    for png in pngs:
        gt = png.with_suffix("").with_suffix(".gt.txt")
        if gt.exists() and gt.read_text(encoding="utf-8").strip():
            filled += 1
    return filled, len(pngs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="affiche seulement l'avancement de la transcription",
    )
    args = parser.parse_args()

    if not args.status:
        if not LINES_DIR.exists():
            raise SystemExit(
                f"{LINES_DIR} est introuvable. Lancez d'abord le pipeline "
                "(python -m cadastron.pipeline) pour extraire les lignes."
            )
        total, created = collect()
        print(f"{total} lignes rassemblees dans {GT_DIR}")
        print(f"{created} fichiers .gt.txt vides crees")

    filled, total = status()
    print(f"Transcription : {filled}/{total} lignes renseignees")
    if filled < 300:
        print(
            "Comptez quelques centaines de lignes transcrites avant de lancer "
            "le fine-tuning (training/finetune_cadastre.py)."
        )


if __name__ == "__main__":
    main()
