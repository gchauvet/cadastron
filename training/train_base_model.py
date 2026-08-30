"""Entraîne un modèle de reconnaissance Kraken de base sur le corpus TIMEUS
(registres administratifs français pré-imprimés, XIXe siècle — même genre
de document que notre cadastre napoléonien, produit avec le même outillage
eScriptorium + Kraken, mais un contenu différent : Prud'hommes/textile
plutôt que cadastre).

Ce modèle de base servira ensuite de point de départ pour un fine-tuning sur
nos propres lignes transcrites du cadastre (voir cadastron/recognize.py et
--rec-model dans cadastron/pipeline.py une fois ce fine-tuning fait).

Prérequis : `pip install kraken`, et avoir lancé `prepare_timeus.py` une
fois pour placer les images à côté de leurs PAGE-XML.

Usage:
    python training/train_base_model.py --device cpu
    python training/train_base_model.py --device cuda:0
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CORPUS_ROOT = Path(__file__).parent / "timeuscorpus" / "data"
SUBCORPORA = ["cph_paris_tissage_1858", "cph_paris_tissage_1878"]
MODELS_DIR = Path(__file__).parent / "models"


def collect_xml_files() -> list[Path]:
    files: list[Path] = []
    for name in SUBCORPORA:
        page_dir = CORPUS_ROOT / name / "page"
        files.extend(sorted(p for p in page_dir.glob("*.xml") if p.name != "METS.xml"))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--device", default="cpu", help="cpu, cuda:0, mps... (defaut: cpu)")
    parser.add_argument("--output", default=str(MODELS_DIR / "timeus_base"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    xml_files = collect_xml_files()
    if not xml_files:
        print("Aucun fichier XML trouve. Avez-vous lance prepare_timeus.py ?", file=sys.stderr)
        sys.exit(1)
    print(f"{len(xml_files)} pages PAGE-XML trouvees pour l'entrainement.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ketos",
        "-d", args.device,
        "--workers", str(args.workers),
        "train",
        "-f", "page",
        "-B", str(args.batch_size),
        "-o", args.output,
        *[str(p) for p in xml_files],
    ]
    print("Commande:", " ".join(f'"{c}"' if " " in c else c for c in cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
