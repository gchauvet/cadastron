"""Prépare le corpus TIMEUS (cloné dans training/timeuscorpus) pour
l'entraînement Kraken/ketos.

Chaque PAGE-XML référence son image par le seul nom de fichier
(`imageFilename="PH 1858-1.jpg"`), mais dans ce dépôt les images vivent au
niveau du sous-corpus alors que les XML sont dans son sous-dossier page/ —
`ketos train -f page` cherche l'image dans le même dossier que le XML.

Ce script place donc un lien (ou une copie si le lien échoue, par ex.
volumes différents) de chaque image à côté de son XML correspondant, sans
toucher aux fichiers originaux.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

CORPUS_ROOT = Path(__file__).parent / "timeuscorpus" / "data"
SUBCORPORA = ["cph_paris_tissage_1858", "cph_paris_tissage_1878"]


def link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> None:
    for name in SUBCORPORA:
        base = CORPUS_ROOT / name
        page_dir = base / "page"
        if not page_dir.exists():
            print(f"skip {name}: pas de dossier page/")
            continue

        count = 0
        for xml_path in page_dir.glob("*.xml"):
            if xml_path.name == "METS.xml":
                continue
            image_path = base / f"{xml_path.stem}.jpg"
            if not image_path.exists():
                print(f"  image manquante pour {xml_path.name}")
                continue
            link_or_copy(image_path, page_dir / image_path.name)
            count += 1
        print(f"{name}: {count} paires image/xml pretes dans {page_dir}")


if __name__ == "__main__":
    main()
