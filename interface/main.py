
import sys
import os
from pathlib import Path

# Находим папку с плагинами Qt
plugins_path = (
    Path(sys.prefix)
    / "Lib"
    / "site-packages"
    / "PyQt5"
    / "Qt5"
    / "plugins"
)

# Указываем Qt правильный путь ДО импорта QApplication
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins_path)

from PyQt5.QtWidgets import QApplication

from interface.MainWindow import MainWindow
from interface.Styles import apply_styles


def main():
    app = QApplication(sys.argv)

    apply_styles(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()