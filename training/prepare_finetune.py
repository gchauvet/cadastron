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
    python training/prepare_finetune.py --lines-per-page 40
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


def select_spread(paths: list[Path], cap: int | None) -> list[Path]:
    """Au plus `cap` lignes, reparties sur toute la hauteur de la page.

    Les noms de fichiers commencent par le numero de ligne du tableau, donc la
    liste triee suit la page de haut en bas : prendre les `cap` premieres ne
    donnerait que le haut du tableau, bloc d'en-tete imprime compris. Un pas
    regulier echantillonne au contraire toutes les hauteurs, et reste
    deterministe -- relancer le script avec le meme plafond redonne exactement
    la meme selection.
    """
    if cap is None or cap <= 0 or len(paths) <= cap:
        return paths
    step = len(paths) / cap
    return [paths[int(i * step)] for i in range(cap)]


def collect(lines_per_page: int | None = None) -> tuple[int, int, int]:
    """Rassemble les lignes et cree les .gt.txt manquants.

    Renvoie (nombre de lignes retenues, nombre de .gt.txt crees, pages vues).
    """
    GT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    created = 0
    pages = 0
    for sheet_dir in sorted(p for p in LINES_DIR.iterdir() if p.is_dir()):
        pages += 1
        for png in select_spread(sorted(sheet_dir.glob("*.png")), lines_per_page):
            # Prefixe par la page pour eviter les collisions entre onglets.
            dst = GT_DIR / f"{sheet_dir.name}__{png.name}"
            link_or_copy(png, dst)
            gt = dst.with_suffix("").with_suffix(".gt.txt")
            if not gt.exists():
                gt.write_text("", encoding="utf-8")
                created += 1
            total += 1
    return total, created, pages


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
    parser.add_argument(
        "--lines-per-page",
        type=int,
        default=None,
        help="ne retenir que N lignes par page, reparties sur toute sa hauteur "
        "(defaut: toutes)",
    )
    args = parser.parse_args()

    if args.lines_per_page is not None and args.lines_per_page < 1:
        parser.error("--lines-per-page doit valoir au moins 1")

    if not args.status:
        if not LINES_DIR.exists():
            raise SystemExit(
                f"{LINES_DIR} est introuvable. Lancez d'abord le pipeline "
                "(python -m cadastron.pipeline) pour extraire les lignes."
            )
        total, created, pages = collect(args.lines_per_page)
        print(f"{total} lignes rassemblees dans {GT_DIR} ({pages} pages)")
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
