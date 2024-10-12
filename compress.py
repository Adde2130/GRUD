import zipfile
import math
import os
import shutil

'''Rough estimations for SLP file compression'''

LZMA_RATIO = 0.13963562606

ZLIB_RATIO = 0.23253719347

# NOTE: This is BLAZINGLY fast, and is prefferable if size isn't an issue
BZIP2_RATIO = 0.21835793841

MARGIN = 0.9

def __divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def get_folder_size(path: str):
    size = 0
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        size += os.path.getsize(file_path)

    return size

#TODO: MULTIPROCESSED COMPRESSION OF SPLIT ARCHIVES
def compress_folder(path: str, size_limit: int) -> int: # Returns number of archives made
    size = get_folder_size(path)
    archives = 1

    if size * BZIP2_RATIO < size_limit * MARGIN: 
        comp_algo = zipfile.ZIP_BZIP2
    else:
        comp_algo = zipfile.ZIP_LZMA

        if size * LZMA_RATIO > size_limit * MARGIN:
            while size * LZMA_RATIO / archives > size_limit * MARGIN:
                archives += 1
                if archives > 5:
                    print("DISASTER WHILE TRYING TO COMPRESS. TELL ADDE")
                    return 0

    if archives == 1: # Create one archive. Easy.
        with zipfile.ZipFile(f"{path}.zip", "w", comp_algo, compresslevel=9) as zipf: # compresslevel does nothing with LZMA
            for file in os.listdir(path):
                zipf.write(f"{path}/{file}", arcname=file)

    else: # Create multiple archives. Annoying.
        files = os.listdir(path)
        parts = __divide_chunks(files, math.ceil(len(files) / archives))
        for i, part in enumerate(parts):
            with zipfile.ZipFile(f"{path} part {i + 1}.zip", "w", comp_algo, compresslevel=9) as zipf: # compresslevel does nothing with LZMA
                for file in part:
                    zipf.write(f"{path}/{file}", arcname=file)

    shutil.rmtree(path)
    print(f"{path} zipped")

    return archives

