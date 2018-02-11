@ECHO OFF 
REM Runs both my project scripts

REM SFX/Voice, Language, Originals Path, 

set SectionName="DesertMission"
set StepsUpToCommonDirectory=1

C:\Python27\Python.exe ImportNewAudioFilesAsDialogue_VR2_automated.py %SectionName% %StepsUpToCommonDirectory%
ECHO Ran Import
PAUSE