start call "RunWwiseCLI.bat"
ECHO Running Wwise CLI, creating WAAPI connection
timeout 5
ECHO Running clean and import
call "CleanMissingOriginals.bat"
call "ImportNewAudioFilesAsDialogue_VR2_automated.bat"
ECHO Ran everything
PAUSE
taskkill /t
