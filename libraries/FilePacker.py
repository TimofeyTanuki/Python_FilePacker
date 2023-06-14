# Импортируем всё из заранее подготовленной библиотеки.
from HuffmanTree import * # https://github.com/TimofeyTanuki/Python_Structures/

# Класс, позволяющий сжимать и распаковывать сжатые файлы.
class FilePacker:

    packed_extension = "packed" # Расширение сжатого файла.
    unpacked_prefix = "unpacked_" # Расширение сжатого файла.
    
    # Метод для упаковки файла.
    def pack(path, encoding = "UTF-8", newPath = None):
        file = open(path, "r", encoding = encoding) # Открываем исходный файл.

        # Определяем название упакованного файла.
        if newPath: newPath += "." + FilePacker.packed_extension
        else: newPath = path + "." + FilePacker.packed_extension
        
        charactersCount = 0 # Счётчик символов в исходном файле.
        
        # Заполняем частотный словарь.
        charactersFrequency = dict()
        while line := file.readline():
            for char in line:
                if char in charactersFrequency: charactersFrequency[char] += 1
                else: charactersFrequency[char] = 1
                charactersCount += 1 # Попутно считаем количество символов в исходном файле.

        # Генерируем двоичные коды для упаковки на базе дерева Хаффмана.
        newHuffmanTree = HuffmanTree()
        for char, count in charactersFrequency.items():
            newHuffmanTree.insert((count, char))
        codesDictionary = newHuffmanTree.getCodesDictionary()

        file.seek(0) # Сбрасываем указатель исходного файла на начало для повторного чтения.
        newFile = open(newPath, "wb") # Создаём файл, в который будет упакован количество записей в частотном словаре, сам словарь, количество символов в исходном файле и упакованное содержимое.

        # Создаём словарь, которым файл будет распаковываться.
        codesList = codesDictionary.items()
        codesCount = len(codesList)

        newFile.write(codesCount.to_bytes(2, "big")) # Записываем количество элементов в словаре распаковки.
        
        # Записываем словарь для распаковки в файл.
        for char, code in codesList:
            """
                Запись одного элемена словаря состоит из:
                * 1 байт - длина двоичного кода
                * 2 байт - двоичный код
                * 1 байт - количество байт, которыми закодирован исходный символ
                * N байт (значение выше) - исходный символ
            """
            charEncoded = char.encode(encoding) # Закодированный исходный символ.
            newFile.write(len(code).to_bytes(1, "big") + int(code, 2).to_bytes(2, "big") + len(charEncoded).to_bytes(1, "big") + charEncoded)

        newFile.write(charactersCount.to_bytes(4, "big")) # Записываем исходное количество символов в файл.

        # Записываем сжатый зашифрованный текст блоками по 32 байта (+1 блок в 1 байт для определения количества значимых нулей в последующем блоке текста).
        chunk = ""
        while line := file.readline():
            for char in line:
                code = codesDictionary[char]
                chunk += code
                if len(chunk) >= 255:
                    zeros = 0
                    for bit in chunk:
                        if bit == "1": break
                        zeros += 1
                    newFile.write(zeros.to_bytes(1, "big"))
                    newFile.write(int(chunk[:255], 2).to_bytes(32, "big"))
                    chunk = chunk[255:]
        
        # Дописываем оставшиеся данные (если они есть) в файл, которые не были записаны при чтении.
        if len(chunk):
            zeros = 0
            for bit in chunk:
                if bit == "1": break
                zeros += 1
            newFile.write(zeros.to_bytes(1, "big"))
            newFile.write(int(chunk[:255], 2).to_bytes(32, "big"))

        # Закрываем файлы и возвращаем путь, по которому был создан сжатый файл.
        newFile.close()
        file.close()
        return newPath

    # Метод для восстановления исходного файла из сжатого.
    def unpack(path, newPath = None, encoding = "UTF-8"):

        # Проверяем файл на соответствие расширению.
        fullPathSplit = path.split("/")
        pathSplit = fullPathSplit[-1].split(".")
        if pathSplit[-1].lower() != FilePacker.packed_extension: raise Exception("Расширение упакованного файла должно быть \"{0}\".".format(FilePacker.packed_extension))

        # Определяем название распакованного файла.
        if path == newPath: raise Exception("Путь распакованного файла должен отличаться от путя запакованного файла.")
        else:
            pathSplit = FilePacker.unpacked_prefix + ".".join(pathSplit[:-1])
            fullPathSplit[-1] = pathSplit
            newPath = "/".join(fullPathSplit)

        file = open(path, "rb") # Открываем сжатый файл.
        newFile = open(newPath, "w", encoding = encoding) # Создаём файл, в который будет распаковано содержимое.
        codesCount = int.from_bytes(file.read(2), "big") # Получаем количество записей, которые находятся в словаре.
        
         # Читаем словарь для расшифровки.
        codesDictionary = dict()
        for i in range(codesCount):
            codeLength = int.from_bytes(file.read(1), "big")
            code = bin(int.from_bytes(file.read(2), "big"))[2:].rjust(codeLength, "0")
            char = b''
            for j in range(int.from_bytes(file.read(1), "big")): char += file.read(1)
            codesDictionary[code] = char.decode(encoding)

        charactersCount = int.from_bytes(file.read(4), "big") # Получаем количество символов, которое должно быть в исходном тексте.

        # Читаем сжатые данные, расшифровываем и параллельно пишем в новый файл пока не кончатся блоки, либо не будет восстановлено исходное количество символов.
        bits = ""
        while (zeros := file.read(1)) and charactersCount:
            zeros = int.from_bytes(zeros, "big")
            bits += "0" * zeros + bin(int.from_bytes(file.read(32), "big"))[2:]
            bitsLength = len(bits)
            endIndex = 1
            while endIndex < bitsLength and charactersCount:
                code = bits[0:endIndex]
                if code in codesDictionary:
                    newFile.write(codesDictionary[code])
                    bits = bits[endIndex:]
                    charactersCount -= 1
                    bitsLength -= endIndex - 1
                    endIndex = 1
                else: endIndex += 1

        # Закрываем файлы и возвращаем путь, по которому был создан распакованный файл.
        newFile.close()
        file.close()
        return newPath