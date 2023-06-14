# Импортируем всё из библиотеки.
from FilePacker import *

# Тест класса для упаковки и распаковки файлов.
encoding = "UTF-8"

# Упаковываем исходный файл.
packedFilePath = FilePacker.pack("tests/FileToPack.txt", encoding, "tests/PackedFile.txt")
print("FilePacker.pack:", packedFilePath)

 # Распаковываем упакованный файл.
print("FilePacker.unpack:", FilePacker.unpack(packedFilePath, "tests/UnpackedFile.txt", encoding))