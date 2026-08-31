# Après la transcription

Ce que devient le travail des bénévoles une fois les `.gt.txt` remplis : la
séquence d'entraînement, ce que chaque mesure signifie réellement, et les
décisions à prendre **avant** que la saisie ne commence pour de bon.

La notice destinée aux transcripteurs est dans [TRANSCRIPTION.md](TRANSCRIPTION.md).

---

## La séquence

### 1. Fine-tuning

```bash
python training/finetune_cadastre.py --device cuda:0
```

Le script ne ramasse que les images dont le `.gt.txt` est **non vide** : les
milliers de fichiers laissés vides sont ignorés sans aucun risque, ce qui rend
la consigne « dans le doute, laissez vide » sûre par construction. Il refuse de
démarrer sous 100 lignes (`--min-lines`).

Il met de côté les pages de validation (voir plus bas), puis lance :

```
ketos train -f path -i <McCATMuS> --resize union -B 8 -o training/models/cadastre \
    -e training/models/validation_lines.txt <lignes d'entrainement...>
```

`--resize union` conserve l'alphabet de McCATMuS et y ajoute les caractères
propres au cadastre — dont le `/` du ditto — au lieu de repartir d'un alphabet
neuf, ce qui détruirait le transfert d'apprentissage. L'arrêt est automatique
(*early stopping* est le défaut de `ketos`) : il n'y a pas de nombre d'époques à
choisir.

Sortie : `training/models/cadastre/best_<précision>.safetensors`.

### 2. Vérification sur banc d'essai indépendant

```bash
python training/eval_model.py --device cuda:0 \
    --model training/models/cadastre/best_0.9xxx.safetensors
```

TIMEUS n'est pas du cadastre. Ce test ne mesure **pas** si le modèle a appris
votre registre : il vérifie qu'il n'a pas *désappris* le reste. C'est un
garde-fou contre l'oubli catastrophique.

| Modèle | Précision caractère | Précision mot |
|---|---|---|
| McCATMuS, sans entraînement | 91,2 % | 73,8 % |
| Entraîné de zéro sur TIMEUS (248 pages, 5 h GPU) | 27,3 % | — |

Un effondrement du modèle affiné vers 60 % signalerait un sur-apprentissage sur
un échantillon trop étroit.

### 3. Reconnaissance sur tout le volume

```bash
python -m cadastron.pipeline \
    --rec-model training/models/cadastre/best_0.9xxx.safetensors
```

Les cellules de l'ODS se remplissent automatiquement.

---

## L'échantillon : comment il a été constitué

Le premier lot disponible — 1393 rognages — venait des **scans 1 à 4**, sept
pages seulement. Probablement une ou deux mains, une seule encre, un seul état de
conservation. Un modèle entraîné là-dessus aurait très bien lu ces sept pages et
nettement moins bien les ~200 autres pages de matrice du volume.

Le principe est constant en apprentissage automatique :

> **30 lignes sur 50 pages valent mieux que 1200 lignes sur 4 pages.**
> À volume de saisie égal, la diversité des mains compte davantage que le nombre
> d'exemples.

Ordre de grandeur visé : **1500 à 2000 lignes transcrites, réparties sur 40 à 60
pages** prises dans toute l'étendue de la matrice (scans ~2 à ~200).

Le pipeline lancé sans option produirait environ 40 000 rognages, bien plus que
ce que des bénévoles peuvent absorber. D'où l'option d'échantillonnage :

```bash
python -m cadastron.pipeline --stride 8
```

`--stride N` ne traite qu'un scan sur N, **étalé sur tout le volume**. Sur 384
scans, un pas de 8 en retient 48, soit 96 pages, dont une cinquantaine de
matrice une fois écartés les autres formulaires — réparties du début à la fin du
registre, donc plusieurs mains et plusieurs états de conservation.

`--stride` choisit *où* regarder dans le volume, `--limit` *combien* en prendre ;
les deux se combinent, l'échantillonnage s'appliquant en premier.

À raison d'environ 200 rognages par page, cela fait tout de même un lot de
l'ordre de 10 000 lignes — le pipeline découpe tout, puisque l'ODS a besoin de
toutes les cellules. Le plafond se pose donc à l'étape suivante, au moment de
constituer le dossier remis aux bénévoles :

```bash
python training/prepare_finetune.py --lines-per-page 40
```

`--lines-per-page N` ne recopie que N lignes par page, **réparties sur toute la
hauteur de la page** et non les N premières : les noms de fichiers commencent par
le numéro de ligne du tableau, si bien que les premières sont toujours le bloc
d'en-tête imprimé. Sur 45 pages de matrice, un plafond de 40 donne ≈ 1 800
lignes — la cible ci-dessus — dans un dossier consultable de bout en bout.

La sélection est déterministe : relancer le script avec le même plafond redonne
exactement les mêmes fichiers, et le relancer avec un plafond plus élevé ajoute
des lignes sans jamais toucher aux transcriptions déjà saisies.

### Ce que le passage a réellement donné

`--stride 8` a retenu 48 scans sur 384, soit 96 pages, dont **47 exploitables** :

| Pages | Sort |
|---|---|
| 47 | retenues, écrites dans l'ODS |
| 46 | tableau de classement (scans 201 à 377) — rejet attendu |
| 1 | `1_a`, édition ancienne de la matrice |
| 2 | `41_a` et `41_b` — **seules vraies pertes**, grille non reconnue |

Sur les 50 pages de matrice échantillonnées, 47 sont donc exploitables : 6 % de
perte, en deçà des 8 % attendus. Elles s'étalent des scans 1 à 193, c'est-à-dire
sur toute l'étendue de la matrice.

Avec les six pages du premier passage, le dossier de saisie compte **53 pages**
et **2 121 lignes** (40 par page, plus une transcription antérieure conservée) —
dans la fourchette visée.

À noter : la moitié du balayage (23 scans sur 48) est tombée dans le tableau de
classement, intégralement rejeté. Sans conséquence ici puisque la cible est
atteinte, mais s'il fallait un jour davantage de matrice, mieux vaudrait un pas
plus serré borné aux scans 1 à 200.

---

## Le jeu de validation : quatre pages mises de côté

Laissé à lui-même, `ketos` découpe une fraction des lignes **au hasard** pour
valider. Ces lignes sortent alors des mêmes pages que celles d'entraînement, et
le `best_0.97` affiché mesure surtout la capacité du modèle à relire des pages
qu'il a déjà vues — pas à lire une page nouvelle, qui est la seule chose qui
compte ici. Deux lignes voisines partagent la main, l'encre et l'état du papier :
tirées au hasard, elles ne valident rien.

Quatre **pages entières** sont donc exclues de l'entraînement, listées dans
[`training/validation_pages.txt`](training/validation_pages.txt) et passées à
`ketos` via `-e/--evaluation-data` :

| Page | Position dans le corpus |
|---|---|
| `1_b` | 1ʳᵉ page sur 53 |
| `33_a` | 14ᵉ |
| `89_b` | 27ᵉ |
| `145_a` | 40ᵉ |

Soit 161 lignes, étalées du début à la fin de la matrice. `--val-pages N` change
le nombre de pages réservées, `--reset-val-pages` recalcule la liste.

> **Ces quatre pages doivent être transcrites comme les autres.** Elles ne servent
> pas à l'entraînement, mais sans transcription la validation n'a rien à mesurer :
> le script refuse alors de démarrer. Si la saisie doit être priorisée, c'est sur
> celles-là.

Une fois la liste écrite, **ne la modifiez plus**. Elle est versionnée pour cette
raison : changer les pages réservées entre deux entraînements rendrait leurs
précisions incomparables, et une page passée par l'entraînement ne peut plus
servir à valider quoi que ce soit.

---

## Ce qui manquera encore après

- **La résolution du signe ditto.** Les `/` seront transcrits fidèlement mais
  resteront des `/` dans l'ODS. Le post-traitement colonne par colonne — qui
  remonte à la première valeur non-ditto au-dessus, dans la même colonne — n'est
  pas écrit.
- **Les autres formulaires du volume.** Le *tableau de classement / application
  du tarif* (~scans 202 à 380, soit la moitié du volume) est correctement
  détecté comme non conforme et ignoré, faute d'un gabarit décrivant sa
  structure de colonnes.
- **~8 % des pages de matrice sont perdues** par le contrôle de qualité de la
  détection de grille. Leur score (11-12 traits reconnus sur 16) recouvre celui
  de pages d'autres formulaires : abaisser le seuil ferait entrer ces dernières.
  La perte est irréductible avec ce critère seul.

---

## Composition du volume, pour mémoire

Le registre réunit quatre formulaires imprimés différents. Seul le deuxième
correspond au gabarit de `cadastron/config.py`.

| Scans | Formulaire |
|---|---|
| 1 | matrice, édition ancienne (deux colonnes en moins) |
| ~2 – 200 | **matrice des propriétés foncières, 15 colonnes** |
| ~202 – 380 | tableau de classement / application du tarif |
| 384 | numéros de parcelles par section |
