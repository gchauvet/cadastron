"""Fine-tune le modèle de base McCATMuS sur les lignes transcrites du cadastre.

C'est la seule étape d'entraînement du projet : McCATMuS lit déjà correctement
l'imprimé du gabarit et sert de point de départ (voir base_model.py), le
fine-tuning ne fait qu'adapter le modèle à l'écriture manuscrite du registre.

Prérequis :
  1. `python -m cadastron.pipeline` pour extraire les lignes ;
  2. `python training/prepare_finetune.py` pour créer les .gt.txt ;
  3. transcrire à la main quelques centaines de lignes.

Quelques pages entieres sont mises de cote pour la validation (voir
ENTRAINEMENT.md) : la precision affichee par `ketos` doit mesurer la capacite du
modele a lire une page qu'il n'a jamais vue, pas a relire celles sur lesquelles
il s'est entraine.

Usage:
    python training/finetune_cadastre.py --device cuda:0
    python training/finetune_cadastre.py --device cpu
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from base_model import ensure_base_model  # noqa: E402
from prepare_finetune import GT_DIR  # noqa: E402

MODELS_DIR = Path(__file__).parent / "models"
# Versionne : une fois fixee, la liste ne doit plus bouger, sinon les
# precisions obtenues d'un entrainement a l'autre ne se comparent plus.
VAL_PAGES_FILE = Path(__file__).parent / "validation_pages.txt"


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


def page_of(png: Path) -> str:
    """`9_b__r024_c05_l00.png` -> `9_b` (le nom de la page d'origine)."""
    return png.name.split("__", 1)[0]


def natural_key(name: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def read_validation_pages() -> list[str] | None:
    if not VAL_PAGES_FILE.exists():
        return None
    pages = [
        line.strip()
        for line in VAL_PAGES_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    return pages or None


def choose_validation_pages(pngs: list[Path], count: int) -> list[str]:
    """`count` pages entieres, etalees sur l'etendue du volume.

    Le choix se fait parmi les pages qui comptent deja des transcriptions,
    faute de quoi le jeu de validation serait vide. Ce qui rend la mesure
    honnete n'est pas que les pages aient ete tirees a l'avance, mais qu'elles
    soient entierement exclues de l'entrainement -- une page, jamais des lignes
    prises au hasard, car deux lignes voisines partagent la main, l'encre et
    l'etat du papier.
    """
    pages = sorted({page_of(p) for p in pngs}, key=natural_key)
    if count >= len(pages):
        raise SystemExit(
            f"{count} pages de validation demandees mais seulement {len(pages)} "
            "pages transcrites. Transcrivez davantage de pages, ou baissez "
            "--val-pages."
        )
    step = len(pages) / count
    return [pages[int(i * step)] for i in range(count)]


def write_validation_pages(pages: list[str]) -> None:
    VAL_PAGES_FILE.write_text(
        "# Pages entieres reservees a la validation du fine-tuning.\n"
        "# Elles sont exclues de l'entrainement : ne pas modifier cette liste\n"
        "# apres un premier entrainement, sous peine de rendre les precisions\n"
        "# obtenues incomparables entre elles.\n"
        + "\n".join(pages)
        + "\n",
        encoding="utf-8",
    )


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
    parser.add_argument(
        "--val-pages",
        type=int,
        default=4,
        help="nombre de pages entieres reservees a la validation (defaut: 4)",
    )
    parser.add_argument(
        "--reset-val-pages",
        action="store_true",
        help=f"recalcule la liste de {VAL_PAGES_FILE.name} au lieu de la relire",
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

    val_pages = None if args.reset_val_pages else read_validation_pages()
    if val_pages is None:
        val_pages = choose_validation_pages(pngs, args.val_pages)
        write_validation_pages(val_pages)
        print(f"Pages de validation fixees dans {VAL_PAGES_FILE.name}.")

    reserved = set(val_pages)
    train_pngs = [p for p in pngs if page_of(p) not in reserved]
    val_pngs = [p for p in pngs if page_of(p) in reserved]

    if not val_pngs:
        print(
            f"Les pages reservees ({', '.join(val_pages)}) ne comptent aucune "
            "ligne transcrite : la validation serait vide.\n"
            "Faites transcrire ces pages, ou relancez avec --reset-val-pages "
            "pour en choisir d'autres.",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(train_pngs) < args.min_lines:
        print(
            f"Il ne reste que {len(train_pngs)} lignes pour l'entrainement une "
            f"fois les {len(val_pages)} pages de validation mises de cote "
            f"(minimum {args.min_lines}). Transcrivez davantage, ou baissez "
            "--val-pages.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"{len(train_pngs)} lignes d'entrainement, "
        f"{len(val_pngs)} lignes de validation."
    )
    print(f"Pages reservees a la validation : {', '.join(val_pages)}")
    if len(val_pngs) < 30:
        print(
            f"Attention : {len(val_pngs)} lignes de validation seulement, la "
            "precision affichee sera bruitee."
        )

    base = Path(args.base_model) if args.base_model else ensure_base_model()
    print(f"Modele de depart : {base}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    # `-e` attend un fichier listant les chemins, pas les chemins eux-memes.
    val_manifest = MODELS_DIR / "validation_lines.txt"
    val_manifest.write_text(
        "\n".join(str(p) for p in val_pngs) + "\n", encoding="utf-8"
    )

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
        # Jeu de validation impose : sans `-e`, ketos tire lui-meme des lignes
        # au hasard dans les memes pages que l'entrainement, et affiche une
        # precision qui mesure sa capacite a relire des pages deja vues.
        "-e", str(val_manifest),
        *[str(p) for p in train_pngs],
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
