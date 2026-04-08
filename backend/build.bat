cd ../frontend  
call npm run build  
cd ../backend  
pyinstaller --clean --noconfirm --name QuestorExplorer --onefile --add-data ../frontend/dist;dist main_exe_runner.py  
mkdir ../Pacote_Empresa  
copy dist\QuestorExplorer.exe ..\Pacote_Empresa\ 
