@ECHO OFF 
REM Runs both my project scripts

REM SFX/Voice, Language, Originals Path, 

set SectionName="DesertMission"
set WwiseProjectRootDir="Wwise_Project/WAAPI_Test"
set StepsUpToCommonDirectory=1

C:\Python27\Python.exe CleanMissingOriginals.py %SectionName% %WwiseProjectRootDir% %StepsUpToCommonDirectory%
ECHO Ran Clean
PAUSE
