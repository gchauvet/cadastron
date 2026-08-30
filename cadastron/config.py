"""Static configuration: the printed column template of the Napoleonic
cadastral "matrice des propriétés foncières" register, and pipeline paths.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    key: str
    header: str
    weight: float  # relative width, used only as a fallback when the printed
                   # grid lines can't be auto-detected from the scan


COLUMNS: list[Column] = [
    Column("numero", "N°", 0.035),
    Column("noms_proprietaires", "Noms, prénoms, professions et demeures des propriétaires", 0.19),
    Column("numero_plan", "N° du plan", 0.06),
    Column("lieux_dits", "Noms des pièces, cantons ou lieux-dits", 0.12),
    Column("noms_fermes", "Noms des fermes", 0.07),
    Column("nature", "Nature des propriétés", 0.07),
    Column("contenance_ha", "Contenance - hectares", 0.035),
    Column("contenance_a", "Contenance - ares", 0.035),
    Column("contenance_ca", "Contenance - centiares", 0.035),
    Column("classement_chiffres", "Classement en chiffres", 0.035),
    Column("classement_lettres", "Classement en toutes lettres", 0.07),
    Column("revenu", "Revenu", 0.06),
    Column("portes_charretieres", "Portes cochères, charretières et de magasin", 0.06),
    Column("portes_fenetres", "Portes et fenêtres ordinaires", 0.06),
]

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
