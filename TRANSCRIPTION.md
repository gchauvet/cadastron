# Transcrire le cadastre

**Notice à l'usage des bénévoles.** Comment recopier les lignes du registre cadastral napoléonien pour apprendre à l'ordinateur à les lire tout seul.

---

## Ce que vous allez faire

Le registre a été photographié page par page, puis découpé automatiquement en milliers de petites images. Chaque image contient **une seule ligne d'écriture**, prélevée dans une case du tableau.

À côté de chaque image se trouve un fichier texte qui porte le même nom, terminé par `.gt.txt`. Il est vide. Votre travail tient en une phrase : **ouvrir l'image, lire la ligne, et taper dans le fichier texte ce que vous avez lu.**

1. Ouvrez l'image, par exemple `2_b__r006_c05_l00.png`.
2. Ouvrez le fichier texte du même nom, `2_b__r006_c05_l00.gt.txt`.
3. Tapez ce que vous lisez sur l'image, puis enregistrez.
4. Passez à l'image suivante. Il n'y a rien d'autre à faire.

### Pourquoi ce travail est utile

L'ordinateur apprend à lire cette écriture **par l'exemple**. Chaque ligne que vous transcrivez est un exemple de plus. Au bout de quelques centaines, il commence à déchiffrer seul le reste du registre — plusieurs centaines de pages que personne n'aura à recopier à la main.

D'où la seule chose qui compte vraiment : **un exemple juste ou rien du tout.** Un fichier laissé vide ne coûte rien, il est simplement ignoré. Un fichier mal rempli, lui, enseigne quelque chose de faux et abîme le travail de tout le monde.

---

## Les trois règles

### 1. Recopiez exactement ce que vous voyez

Pas de correction d'orthographe, pas de mise au goût du jour, pas d'abréviation développée. Si le clerc a écrit `pommeray`, vous tapez `pommeray` — même si vous savez qu'on écrirait « pommeraie » aujourd'hui. Gardez les majuscules et les accents tels qu'ils sont sur la page.

### 2. Une image = une ligne

Le découpage est rectangulaire : il mord souvent sur la ligne du dessus ou celle du dessous, et parfois sur la colonne d'à côté. **Seule compte la ligne qui occupe le centre de l'image.** Tout ce qui n'est qu'un fragment sur un bord ne se transcrit pas.

### 3. Dans le doute, laissez vide

Illisible, ambigu, deux lignes également présentes, aucune vraiment au centre ? Laissez le fichier vide et passez à la suivante. C'est une réponse parfaitement valable, et de loin la plus utile en cas d'hésitation.

---

## Cas par cas

De vrais exemples tirés du registre, avec ce qu'il faut taper dans chaque cas.

### ✅ À transcrire — `Terre`

![Ligne manuscrite isolée portant le mot Terre](docs/notice/ok-terre.png)

Le cas idéal : **un seul mot, bien au centre, rien qui dépasse.** Vous tapez le mot, vous enregistrez, c'est fini.

### ✅ À transcrire — `de la pommeray`

![Ligne manuscrite portant les mots « de la pommeray »](docs/notice/ok-pommeray.png)

Plusieurs mots, c'est **normal et même souhaitable**. L'ordinateur lit des lignes entières, jamais des lettres isolées : plus la ligne est longue, plus elle lui apprend de choses. Ne découpez rien.

### ✅ À transcrire — `Trois`

![Ligne manuscrite portant le mot Trois](docs/notice/ok-trois.png)

La majuscule initiale est celle de la page : on la garde. On ne rajoute pas de point final s'il n'y en a pas.

### ✅ À transcrire — `Pouzauges`

![Ligne manuscrite portant le mot Pouzauges, avec un fragment de la ligne du dessus visible en haut](docs/notice/ok-pouzauges.png)

Un morceau de la ligne du dessus dépasse en haut de l'image. **On l'ignore** : il appartient à une autre ligne, qui a sa propre image et son propre fichier. Seul `Pouzauges`, au centre, se transcrit.

### ⬜ Laisser vide — deux cases séparées par un trait

![Image contenant deux mots manuscrits séparés par un trait vertical imprimé](docs/notice/vide-deux-cases.png)

Deux mots séparés par un **trait vertical imprimé** : ce trait est une frontière de colonne, les deux mots appartiennent à deux cases différentes. Les taper tous les deux apprendrait à l'ordinateur à lire à travers les colonnes et à mélanger les cases. Fichier vide.

### ⬜ Laisser vide — une ligne entière du tableau

![Image couvrant une ligne entière du tableau, traversant plusieurs traits verticaux](docs/notice/vide-ligne-entiere.png)

Même problème en pire : l'image traverse **toute la largeur du tableau** et plusieurs colonnes à la fois. Elle ne correspond à aucune case. Fichier vide.

### ⬜ Laisser vide — texte imprimé

![Texte imprimé en capitales espacées : des Propriétaires](docs/notice/vide-entete-imprime.png)

Ceci est du **texte imprimé**, l'en-tête du formulaire — et non de l'écriture à la main. L'ordinateur doit apprendre l'écriture manuscrite ; lui montrer des caractères d'imprimerie ne sert à rien. On le reconnaît à son gris uniforme, ses lettres espacées et régulières, et son alignement parfaitement horizontal.

### ⬜ Laisser vide — illisible

![Fragment d'encre illisible, sans mot identifiable](docs/notice/vide-illisible.png)

Quelques traces d'encre, aucun mot lisible au centre. **N'essayez pas de deviner.** Fichier vide, on passe à la suite.

### ⚠️ Le bloc d'en-tête, en début de page

Les **trois à six premières images de chaque page** sont presque toujours l'en-tête imprimé du formulaire : `NOMS`, `CONTENANCES`, `des Propriétaires.`, `LIEUX DITS.` et ainsi de suite. Toutes sont à laisser vides.

C'est le piège le plus fréquent, parce que ces images arrivent en premier dans la liste. Passez-les sans hésiter : l'écriture à la main commence juste après.

---

## Taches, ratures et gribouillis

Le registre a deux cents ans. Il porte des taches d'encre, des ratures, des repentirs du clerc, des passages où le papier a bu. C'est normal, et **ce n'est pas un défaut de l'image**.

Devant une image un peu sale, on est tenté de la nettoyer avant de la transcrire. **Ne le faites pas.** L'ordinateur devra lire de vraies pages, taches comprises — c'est précisément sur ces lignes-là qu'il apprend à ne pas confondre une éclaboussure avec une lettre. Une image nettoyée lui enseigne un registre qui n'existe pas, et le laisse démuni devant le vrai.

Une ligne abîmée mais lisible est donc un **excellent** exemple, l'un des plus utiles que vous puissiez donner. Tout se joue dans le fichier texte, jamais sur l'image :

| Ce que vous voyez | Ce que vous faites |
|---|---|
| La tache gêne, mais vous lisez la ligne | Tapez ce que vous lisez, sans toucher à l'image |
| La tache cache des lettres | Laissez le fichier vide |
| Vous devinez les lettres cachées grâce aux lignes voisines | Laissez le fichier vide |

Le dernier cas mérite qu'on s'y arrête, car il part d'une bonne intention. Reconstituer un mot d'après la ligne du dessus, c'est taper des lettres dont l'encre n'est pas sur l'image : on apprend alors à l'ordinateur à inventer du texte là où il n'y en a pas. C'est le pire service qu'on puisse lui rendre — bien pire qu'une case laissée vide.

---

## Le signe « même chose »

<img src="repetita.png" alt="Signe ditto manuscrit, en forme de barre oblique" height="60">

Ce signe, qui ressemble à une barre oblique, veut dire « **même valeur que la case juste au-dessus, dans la même colonne** ».

Quand vous le rencontrez, tapez simplement le caractère `/` et rien d'autre. **Ne le remplacez jamais par la valeur qu'il désigne** — c'est l'ordinateur qui s'en chargera plus tard, automatiquement. Vous, vous décrivez seulement ce qui est écrit sur la page.

Attention : il reprend la case du dessus **dans sa colonne**, jamais la ligne entière.

| Lieu-dit | Nature |
|---|---|
| La Pommeray | Terre |
| `/` | Pré |
| `/` | `/` |

Sur la dernière ligne, le premier `/` vaut « La Pommeray » et le second vaut « Pré ». Chacun regarde vers le haut, dans sa propre colonne.

---

## En pratique

- **Ne renommez ni ne déplacez aucun fichier.** L'image et son fichier texte sont appariés par leur nom : le moindre changement casse le lien entre les deux.
- **Ne modifiez jamais les images.** Elles doivent rester exactement telles que l'ordinateur les a découpées. Si l'une d'elles vous paraît vraiment inutilisable, laissez son fichier texte vide et signalez-la au coordinateur, plutôt que de la retoucher.
- **Une seule ligne de texte par fichier**, sans retour à la ligne. Si vous avez besoin d'appuyer sur Entrée, c'est probablement que l'image contient deux lignes — auquel cas laissez-la vide.
- **Enregistrez en UTF-8.** C'est indispensable pour que les accents soient conservés. Dans le Bloc-notes de Windows : `Fichier` → `Enregistrer sous`, puis choisissez `UTF-8` dans la liste « Encodage », en bas de la fenêtre.
- **Inutile de tout faire d'un coup.** Vous pouvez vous arrêter à n'importe quel moment : les fichiers déjà remplis sont conservés, ceux qui restent vides seront repris plus tard.
- **Pas de mise en forme.** Ni gras, ni italique, ni guillemets ajoutés : uniquement les caractères présents sur la page.

### Une hésitation ?

Ne tranchez pas au jugé : laissez le fichier vide et signalez-le au coordinateur. Sur des milliers de lignes, quelques cases vides ne se voient pas. Une lecture inventée, si.

---

Vous n'avez pas à déchiffrer le registre entier. Chaque ligne que vous recopiez fidèlement apprend à l'ordinateur à déchiffrer les suivantes.

---

## Pour le coordinateur

Suivi de l'avancement :

```bash
python training/prepare_finetune.py --status
```

Les fichiers `.gt.txt` déjà remplis ne sont jamais écrasés ; le script peut être relancé après chaque nouveau passage du pipeline. Comptez quelques centaines de lignes transcrites avant de lancer le fine-tuning (voir [README.md](README.md#entraînement-du-modèle)).

Quatre pages — `1_b`, `33_a`, `89_b`, `145_a` — sont réservées à la validation du modèle et exclues de son entraînement (voir [`training/validation_pages.txt`](training/validation_pages.txt)). Elles se transcrivent exactement comme les autres, mais sans elles la précision affichée ne mesurerait rien : si la saisie doit être priorisée, c'est sur celles-là. Leurs fichiers commencent par ces préfixes.

Un défaut d'image **systématique** — voile, contraste faible sur toute une série de scans — relève de `cadastron/preprocess.py`, où il s'applique de la même façon à l'entraînement et à la reconnaissance. C'est la seule retouche légitime : celle qui vaut aussi pour les pages que le modèle lira plus tard. Une correction apportée à un rognage isolé, elle, ne survivrait pas — les images de `cadastre_gt` sont des liens physiques vers `output/lines/` et ne sont pas versionnées, donc invisible pour tout le monde et impossible à reproduire.
