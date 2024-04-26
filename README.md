# blender-python-path-render
## Setting up blender-python

1. Install blender
2. Install python version fitting your blender version
3. create a new venv with specific version and install the requirements
```Windows
py -3.11 -m venv blender-python
source blender-python/bin/activate
pip install pandas
```
4. Install https://github.com/nutti/fake-bpy-module into the venv as well. (You can use a secondary venv for vs-code and just install it there)
5. Install https://github.com/JacquesLucke/blender_vscode in vscode.
6. Scripts that you want to launch in blender need to know about the venv you set up earlier.
```
import sys
sys.path.insert(0, "C:\\path\\to\\blender-python\\lib\\site-packages\\")
```
7. Launch Scripts with VSCode `Ctrl + Shift + P` Blender: Start, `Ctrl + Shift + P` Blender: RunScript
