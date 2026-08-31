@echo off
REM Lance le fine-tuning du modele de reconnaissance dans une console dediee,
REM independante de l'agent : la fenetre survit a la fin de la session.
REM PYTHONUTF8 evite le crash UnicodeEncodeError de l'affichage Rich sous Windows.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"
title Cadastron - fine-tuning cadastre
REM Tee-Object (cmd n'a pas de `tee`) affiche la progression ET l'archive :
REM les diagnostics restent lisibles meme si la fenetre est fermee.
powershell -NoProfile -Command "python finetune_cadastre.py --device cuda:0 2>&1 | Tee-Object -FilePath finetune_log.txt"
echo.
echo === Entrainement termine (code %ERRORLEVEL%) ===
pause
