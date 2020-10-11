# Note: you need the PyAudio .whl and the portaudio_x86.dll files
# in the same directory.

py -3.7 -m venv venv
./venv/Scripts/Activate.ps1
python -m pip install pip
pip install pynput
pip install PyAudio-0.2.11-cp37-cp37m-win_amd64.whl
pip install numpy
pip install sounddevice
pip install scipy
pip install matplotlib