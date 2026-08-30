<p align="center">
  <img src="cadastron.jpg" alt="Logo Cadastron" width="220">
</p>

<h1 align="center">Cadastron</h1>

<p align="center">
  Numérisation et transcription assistée des registres cadastraux napoléoniens.
</p>

---

## Le projet

Les **matrices cadastrales napoléoniennes** sont des registres manuscrits du XIXe siècle, imprimés selon un gabarit fixe de colonnes (numéro de plan, propriétaire, nature, contenances, classement, revenu imposable, portes et fenêtres...) et remplis à la main. Chaque scan haute résolution du registre contient deux pages manuscrites en vis-à-vis, séparées par la gouttière de reliure.

**Cadastron** transforme ces scans en un tableur ODS exploitable, avec un onglet par page manuscrite, en préservant l'intégralité des colonnes imprimées du gabarit d'origine.

## Pipeline

Pour chaque scan (`images/*.jpg`) :

1. **Découpage** — détection automatique de la gouttière de reliure et séparation en deux pages physiques (en mémoire, aucun fichier intermédiaire écrit sur disque).
2. **Redressement** — correction de l'inclinaison de chaque page (`deskew`).
3. **Détection de la grille imprimée** — repérage automatique des 14 colonnes du gabarit à partir des traits imprimés (pas de découpage naïf, calé sur le contenu réel de chaque page).
4. **Segmentation des lignes** — détection des lignes manuscrites avec [Kraken](https://kraken.re/) (`blla`).
5. **Regroupement en lignes de tableau** — association des segments détectés aux bonnes colonnes/lignes de la grille.
6. **Reconnaissance (optionnelle)** — transcription automatique via un modèle Kraken entraîné (voir [Entraînement du modèle](#entraînement-du-modèle) ci-dessous) ; en son absence, les images de chaque ligne sont conservées pour transcription manuelle ou entraînement futur.
7. **Export ODS** — écriture d'un classeur `output/cadastron.ods` avec un onglet par page (~380 pages attendues).

## Structure du projet

```
cadastron/
├── cadastron/            # package principal
│   ├── config.py         # schéma des 14 colonnes du gabarit
│   ├── gutter.py          # détection de la gouttière / découpage en mémoire
│   ├── preprocess.py      # redressement, binarisation
│   ├── columns.py         # détection de la grille de colonnes imprimée
│   ├── segment.py         # segmentation des lignes (Kraken blla)
│   ├── rows.py             # regroupement des lignes en cellules (ligne, colonne)
│   ├── recognize.py       # reconnaissance de texte (Kraken, modèle entraîné)
│   ├── ods_writer.py      # génération du classeur ODS
│   └── pipeline.py        # orchestration bout en bout (CLI)
├── training/               # entraînement du modèle de reconnaissance
│   ├── prepare_timeus.py   # préparation du corpus TIMEUS pour ketos
│   └── train_base_model.py # entraînement d'un modèle de base via ketos
├── images/                 # scans sources (non versionnés)
└── output/                 # classeur ODS + images de lignes générées
```

## Installation

```bash
pip install -r requirements.txt
```

> Sous Windows avec GPU NVIDIA, réinstallez `torch` avec le bon index CUDA si `pip install kraken` a installé une version CPU :
> ```bash
> pip install --index-url https://download.pytorch.org/whl/cu124 --force-reinstall --no-deps torch torchvision
> ```

## Utilisation

```bash
# Pipeline complet sur tous les scans de images/
python -m cadastron.pipeline --images-dir images --output output/cadastron.ods

# Test rapide sur les 2 premiers scans
python -m cadastron.pipeline --limit 2

# Avec un modèle de reconnaissance entraîné
python -m cadastron.pipeline --rec-model training/models/timeus_base_best.mlmodel
```

Sans `--rec-model`, les cellules du tableau restent vides mais chaque ligne détectée est sauvegardée dans `output/lines/<page>/` avec un `layout.json`, afin de pouvoir réconcilier une transcription (manuelle ou automatique) ultérieure avec le classeur.

## Entraînement du modèle

Aucun modèle de reconnaissance manuscrite n'existant pour ce type de document, la stratégie retenue est un **transfert d'apprentissage en deux temps** :

1. **Modèle de base** — entraîné sur le [corpus TIMEUS](https://github.com/HTR-United/timeuscorpus) (registres administratifs français pré-imprimés du XIXe siècle, Conseil des Prud'hommes de Paris, 1858/1878 — même genre de document, même outillage eScriptorium/Kraken, contenu différent).
   ```bash
   python training/prepare_timeus.py
   python training/train_base_model.py --device cuda:0
   ```
2. **Fine-tuning** — à partir du modèle de base, affinage sur un corpus de lignes réellement issues du cadastre napoléonien, transcrites manuellement à partir des lignes extraites par le pipeline (`output/lines/`).

## État d'avancement

- [x] Découpage automatique de la gouttière et des pages
- [x] Détection automatique de la grille des 14 colonnes (validée sur scans réels)
- [x] Export ODS multi-onglets
- [x] Segmentation des lignes manuscrites (Kraken)
- [ ] Modèle de reconnaissance de base (entraînement en cours sur le corpus TIMEUS)
- [ ] Fine-tuning sur le cadastre napoléonien
- [ ] Traitement bout en bout des ~384 scans / ~768 pages
