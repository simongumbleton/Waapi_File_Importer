@echo off
set SectionName="DesertMission"
set WwiseProjectRootDir="Wwise_Project/WAAPI_Test"
set StepsUpToCommonDirectory=1

CleanMissingOriginals\CleanMissingOriginals.exe %SectionName% %WwiseProjectRootDir% %StepsUpToCommonDirectory%
ECHO Ran Clean
PAUSE