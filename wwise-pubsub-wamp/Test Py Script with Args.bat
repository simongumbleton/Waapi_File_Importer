@ECHO OFF 
REM Runs both my project scripts

REM SFX/Voice, Language, Originals Path, 

set ObjectType="ActorMixer"
set NameConflict="replace"

C:\Python27\Python.exe CreateNewObjects_WithImport_VR2.py %ObjectType% %NameConflict%
ECHO Ran project
PAUSE