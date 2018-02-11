@echo off
set SectionName="DesertMission"
set WwiseProjectRootDir="Wwise_Project/WAAPI_Test"
set StepsUpToCommonDirectory=1

ImportNewAudioFilesAsDialogue_VR2_automated\ImportNewAudioFilesAsDialogue_VR2_automated.exe %SectionName% %WwiseProjectRootDir% %StepsUpToCommonDirectory%
ECHO Ran Importer
PAUSE