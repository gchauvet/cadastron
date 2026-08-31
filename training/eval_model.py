"""Mesure la précision d'un modèle Kraken sur le corpus TIMEUS.

Le corpus TIMEUS (registres administratifs français pré-imprimés du XIXe
siècle, Conseil des Prud'hommes de Paris) n'est pas utilisé pour entraîner :
il sert de banc d'essai indépendant, sur un type de document très proche du
cadastre, pour comparer des modèles sur une même échelle.

Résultats de référence (5 pages, 7490 caractères) :
  - McCATMuS, sans aucun entraînement ......... 91,2 % caractère / 73,8 % mot
  - modèle entraîné de zéro sur TIMEUS ........ 27,3 % caractère

C'est cet écart qui a fait abandonner l'entraînement d'un modèle de base
maison au profit d'un fine-tuning direct de McCATMuS (finetune_cadastre.py).

Prérequis : `python training/prepare_timeus.py` (place les images à côté de
leurs PAGE-XML).

Usage:
    python training/eval_model.py --device cuda:0
    python training/eval_model.py --model training/models/cadastre_best.mlmodel
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from base_model import ensure_base_model  # noqa: E402

CORPUS_ROOT = Path(__file__).parent / "timeuscorpus" / "data"
SUBCORPORA = ["cph_paris_tissage_1858", "cph_paris_tissage_1878"]


def collect_xml_files() -> list[Path]:
    files: list[Path] = []
    for name in SUBCORPORA:
        page_dir = CORPUS_ROOT / name / "page"
        if not page_dir.exists():
            continue
        files.extend(sorted(p for p in page_dir.glob("*.xml") if p.name != "METS.xml"))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--device", default="cpu", help="cpu, cuda:0, mps... (defaut: cpu)")
    parser.add_argument(
        "--model",
        default=None,
        help="modele a evaluer (defaut: McCATMuS, telecharge au besoin)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=5,
        help="nombre de pages de test (defaut: 5 ; 0 = tout le corpus, tres long)",
    )
    args = parser.parse_args()

    xml_files = collect_xml_files()
    if not xml_files:
        print(
            "Aucun fichier XML trouve. Avez-vous lance prepare_timeus.py ?",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.pages > 0:
        xml_files = xml_files[: args.pages]
    print(f"{len(xml_files)} pages PAGE-XML utilisees pour l'evaluation.")

    model = Path(args.model) if args.model else ensure_base_model()
    print(f"Modele evalue : {model}")

    cmd = [
        "ketos",
        "-d", args.device,
        "test",
        "-m", str(model),
        "-f", "page",
        *[str(p) for p in xml_files],
    ]
    print("Commande:", " ".join(f'"{c}"' if " " in c else c for c in cmd))

    # Meme contrainte d'encodage que partout ailleurs sous Windows.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
