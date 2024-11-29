import sys
import os

# Ruta a tu proyecto en PythonAnywhere
project_home = '/home/kevinmaster/project'  # Reemplaza <tu_usuario> por tu nombre de usuario en PythonAnywhere

if project_home not in sys.path:
    sys.path.insert(0, project_home)


from app1 import app as application  

