@ECHO OFF 
REM Runs both my project scripts

REM SFX/Voice, Language, Originals Path, 

set SectionName="DesertMission"

C:\Python27\Python.exe CleanMissingOriginals.py %SectionName%
ECHO Ran Clean
