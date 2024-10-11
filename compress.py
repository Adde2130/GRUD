import zipfile
import os
import shutil

'''Rough estimations for SLP file compression'''

LZMA_RATIO = 0.13963562606

ZLIB_RATIO = 0.23253719347

# NOTE: This is BLAZINGLY fast, and is prefferable if size isn't an issue
BZIP2_RATIO = 0.21835793841


def get_folder_size(path: str):
    size = 0
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        size += os.path.getsize(file_path)

    return size

def compress_folder(path: str, size_limit: int):
    size = get_folder_size(path)

    if size * BZIP2_RATIO < size_limit * 0.9: 
        comp_algo = zipfile.ZIP_BZIP2
    elif size * LZMA_RATIO < size_limit * 0.9:
        comp_algo = zipfile.ZIP_LZMA
    else:
        print("File is too large. Quitting function. TODO: IMPLEMENT ARCHIVE SPLITTING")
        return False

    with zipfile.ZipFile(f"{path}.zip", "w", comp_algo, compresslevel=9) as zipf:
        for file in os.listdir(path):
            zipf.write(f"{path}/{file}", arcname=file)

        shutil.rmtree(path)

    print(f"{path} zipped")

    return True

