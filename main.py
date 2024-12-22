import os
import zlib
import lzma
import tkinter as tk
from tkinter import filedialog, messagebox

def preprocess_data(data):
    """Предварительная обработка данных для оптимизации сжатия."""
    # Удаление лишних пробелов и нормализация строк (например, для текстов)
    if all(32 <= b < 127 for b in data):  # Если данные текстовые
        data = b" ".join(data.split())
    return data

def compress_data(data):
    """Рекурсивное комбинированное сжатие."""
    data = preprocess_data(data)  # Предварительная обработка
    previous_size = len(data)
    max_iterations = 20  # Увеличиваем лимит итераций для более сильного сжатия
    for _ in range(max_iterations):
        zlib_compressed = zlib.compress(data, level=9)
        lzma_compressed = lzma.compress(zlib_compressed, preset=9 | lzma.PRESET_EXTREME)

        current_size = len(lzma_compressed)
        if current_size >= previous_size:
            break  # Прекращаем, если сжатие не улучшает результат

        data = lzma_compressed
        previous_size = current_size

    return data

def create_archive(input_files, archive_name):
    with open(archive_name, 'wb') as archive:
        num_files = len(input_files)
        archive.write(num_files.to_bytes(4, byteorder='little'))

        for file_name in input_files:
            file_name_bytes = file_name.encode('utf-8')
            archive.write(len(file_name_bytes).to_bytes(2, byteorder='little'))
            archive.write(file_name_bytes)

            file_size = os.path.getsize(file_name)
            archive.write(file_size.to_bytes(4, byteorder='little'))

            with open(file_name, 'rb') as f:
                file_data = f.read()
                compressed_data = compress_data(file_data)

                archive.write(len(compressed_data).to_bytes(4, byteorder='little'))
                archive.write(compressed_data)

    messagebox.showinfo("Успех", f"Архив {archive_name} создан и сжат.")

def extract_archive(archive_name, output_dir):
    with open(archive_name, 'rb') as archive:
        num_files = int.from_bytes(archive.read(4), byteorder='little')

        for _ in range(num_files):
            file_name_len = int.from_bytes(archive.read(2), byteorder='little')
            file_name = archive.read(file_name_len).decode('utf-8')
            file_size = int.from_bytes(archive.read(4), byteorder='little')

            compressed_size = int.from_bytes(archive.read(4), byteorder='little')
            compressed_data = archive.read(compressed_size)

            data = compressed_data
            for _ in range(15):  # Увеличиваем лимит попыток декомпрессии
                try:
                    decompressed_lzma = lzma.decompress(data)
                    decompressed_data = zlib.decompress(decompressed_lzma)
                    data = decompressed_data
                except Exception:
                    break

            output_path = os.path.join(output_dir, file_name)
            with open(output_path, 'wb') as f:
                f.write(data)

            messagebox.showinfo("Успех", f"Файл {file_name} извлечен в {output_path}.")

class ArchiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Комбинированный архиватор zlib + lzma")

        self.archive_button = tk.Button(root, text="Выбрать файлы для архивации", command=self.select_files)
        self.archive_button.pack(pady=10)

        self.save_button = tk.Button(root, text="Выбрать папку для сохранения архива", command=self.save_archive)
        self.save_button.pack(pady=10)

        self.extract_button = tk.Button(root, text="Извлечь архив", command=self.extract_files)
        self.extract_button.pack(pady=10)

        self.files_to_archive = []
        self.archive_name = ""

    def select_files(self):
        self.files_to_archive = filedialog.askopenfilenames(title="Выберите файлы", filetypes=[("Файл", "*.*")])
        if self.files_to_archive:
            messagebox.showinfo("Выбор файлов", f"Выбрано {len(self.files_to_archive)} файлов для архивации.")

    def save_archive(self):
        if not self.files_to_archive:
            messagebox.showerror("Ошибка", "Сначала выберите файлы для архивации!")
            return

        self.archive_name = filedialog.asksaveasfilename(defaultextension=".st", filetypes=[("Стичи", "*.st *.stich *.стич")])
        if self.archive_name:
            create_archive(self.files_to_archive, self.archive_name)

    def extract_files(self):
        archive_path = filedialog.askopenfilename(title="Выберите архив для извлечения", filetypes=["Стичи", "*.st .stich *.стич"])
        if not archive_path:
            return

        output_dir = filedialog.askdirectory(title="Выберите папку для извлечения")
        if output_dir:
            extract_archive(archive_path, output_dir)

if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveApp(root)
    root.mainloop()
 