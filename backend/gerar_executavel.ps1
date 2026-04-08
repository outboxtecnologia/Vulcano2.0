Continue = " "Stop  
cd ..\frontend  
call npm run build  
cd ..\backend  
pip install pyinstaller  
pip install -r requirements.txt  
