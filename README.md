# StudiLog

A tool for organizing university courses. The tool is currently only available in german, but support for english is planned.

## Building

Install the required libraries:

```
pip install -r requirements.txt
```

Make sure to generate the necessary python files from the ui files by running:
```
pyuic5 src/ui/mainwindow.ui -o src/ui/mainwindow.py
```

You can then run `src/main.py` to launch the program.

To build an executable for windows:
```
src/setup.py build -b ../build
```

If you want to build for another platform, you will have to look into the cx_freeze documentation and edit `src/setup.py`
accordingly.
