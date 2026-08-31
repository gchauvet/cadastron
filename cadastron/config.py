"""Static configuration: the printed column template of the Napoleonic
cadastral "matrice des propriétés foncières" register, and pipeline paths.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    key: str
    header: str
    weight: float  # width of the column as a fraction of the table width


# The printed form numbers twelve columns, but three of them are subdivided:
# CONTENANCES into hectares/ares/centiares, REVENU into francs/centimes and
# NOMBRE D'OUVERTURES into portes charretières / portes et fenêtres. Fifteen
# physical columns therefore, hence sixteen vertical rules.
#
# The weights are not guesses: they were read rule by rule off the printed
# header of two independent pages (1_b and 116_a), which agreed to within
# 0.005 on all fifteen widths. `columns.py` fits this template onto the rules
# it manages to detect, so these values steer the detection itself — do not
# adjust them without re-measuring against a scan.
COLUMNS: list[Column] = [
    Column("numero", "N° de la liste alphabétique", 0.04269),
    Column("noms_proprietaires", "Noms, prénoms, professions et demeures des propriétaires", 0.21363),
    Column("numero_plan", "N° du plan", 0.04997),
    Column("lieux_dits", "Noms des pièces, cantons ou lieux-dits", 0.14260),
    Column("noms_fermes", "Noms des fermes", 0.09128),
    Column("nature", "Nature des propriétés", 0.07265),
    Column("contenance_ha", "Contenance - hectares", 0.03089),
    Column("contenance_a", "Contenance - ares", 0.03292),
    Column("contenance_ca", "Contenance - centiares", 0.02931),
    Column("classement_chiffres", "Classement en chiffres", 0.04835),
    Column("classement_lettres", "Classement en toutes lettres", 0.09105),
    Column("revenu_francs", "Revenu - francs", 0.04859),
    Column("revenu_centimes", "Revenu - centimes", 0.02591),
    Column("portes_charretieres", "Portes cochères, charretières et de magasin", 0.03906),
    Column("portes_fenetres", "Portes et fenêtres ordinaires", 0.04110),
]

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
