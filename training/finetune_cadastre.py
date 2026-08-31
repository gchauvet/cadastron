"""Fine-tune le modèle de base McCATMuS sur les lignes transcrites du cadastre.

C'est la seule étape d'entraînement du projet : McCATMuS lit déjà correctement
l'imprimé du gabarit et sert de point de départ (voir base_model.py), le
fine-tuning ne fait qu'adapter le modèle à l'écriture manuscrite du registre.

Prérequis :
  1. `python -m cadastron.pipeline` pour extraire les lignes ;
  2. `python training/prepare_finetune.py` pour créer les .gt.txt ;
  3. transcrire à la main quelques centaines de lignes.

Usage:
    python training/finetune_cadastre.py --device cuda:0
    python training/finetune_cadastre.py --device cpu
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from base_model import ensure_base_model  # noqa: E402
from prepare_finetune import GT_DIR  # noqa: E402

MODELS_DIR = Path(__file__).parent / "models"


def collect_transcribed() -> list[Path]:
    """Images de lignes dont le .gt.txt est non vide."""
    if not GT_DIR.exists():
        return []
    kept: list[Path] = []
    for png in sorted(GT_DIR.glob("*.png")):
        gt = png.with_suffix("").with_suffix(".gt.txt")
        if gt.exists() and gt.read_text(encoding="utf-8").strip():
            kept.append(png)
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--device", default="cpu", help="cpu, cuda:0, mps... (defaut: cpu)")
    parser.add_argument("--output", default=str(MODELS_DIR / "cadastre"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument(
        "--base-model",
        default=None,
        help="chemin d'un modele de depart (defaut: McCATMuS, telecharge au besoin)",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=100,
        help="refuse de lancer en dessous de ce nombre de lignes transcrites",
    )
    args = parser.parse_args()

    pngs = collect_transcribed()
    if len(pngs) < args.min_lines:
        print(
            f"Seulement {len(pngs)} lignes transcrites (minimum {args.min_lines}).\n"
            f"Remplissez les .gt.txt dans {GT_DIR}, puis relancez.\n"
            "Avancement : python training/prepare_finetune.py --status",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"{len(pngs)} lignes transcrites utilisees pour le fine-tuning.")

    base = Path(args.base_model) if args.base_model else ensure_base_model()
    print(f"Modele de depart : {base}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ketos",
        "-d", args.device,
        "--workers", str(args.workers),
        "train",
        "-f", "path",
        "-i", str(base),
        # `union` conserve l'alphabet de McCATMuS et y ajoute les caracteres
        # propres au cadastre (dont le signe ditto `/`) au lieu de repartir
        # d'un alphabet neuf, ce qui detruirait le transfert d'apprentissage.
        "--resize", "union",
        "-B", str(args.batch_size),
        "-o", args.output,
        *[str(p) for p in pngs],
    ]
    print("Commande:", " ".join(f'"{c}"' if " " in c else c for c in cmd))

    # Windows redirige stdout vers un encodage cp1252 par defaut, incapable
    # d'encoder les caracteres unicode (ex. "∞") que Rich/Lightning
    # ecrivent dans leur affichage de progression -> force l'UTF-8.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
