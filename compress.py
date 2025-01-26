import zipfile
import math
import os
import shutil
import argparse
import time

'''Rough estimations for SLP file compression'''

LZMA_RATIO = 0.13963562606

ZLIB_RATIO = 0.23253719347

# NOTE: This is BLAZINGLY fast, and is prefferable if size isn't an issue
BZIP2_RATIO = 0.21835793841

MARGIN = 0.9

def __divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def get_folder_size(path: str) -> int:
    size = 0
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        size += os.path.getsize(file_path)

    return size

# TODO: Make thread safe/stoppable from other threads
#      MULTIPROCESSED COMPRESSION OF SPLIT ARCHIVES
#      PERHAPS COMPRESSION IN C FOR FASTER SPEED?
def compress_folder(path: str, size_limit: int, compressed_files=None, remove=True) -> int: # Returns number of archives made
    if size_limit == 0:
        size_limit = 0xFFFFFFFF # 4GB

    size = get_folder_size(path)
    archives = 1

    if size * BZIP2_RATIO < size_limit * MARGIN: 
        comp_algo = zipfile.ZIP_BZIP2
        print(f"Zipping {path} with BZIP2")
    else:
        comp_algo = zipfile.ZIP_LZMA
        print(f"Zipping {path} with LZMA")

        if size * LZMA_RATIO > size_limit * MARGIN:
            print(f"Zipping {path} in multiple parts")
            while size * LZMA_RATIO / archives > size_limit * MARGIN:
                archives += 1

                if size * BZIP2_RATIO / archives > size_limit * MARGIN:
                    comp_algo = zipfile.ZIP_LZMA
                    break

                if archives > 5:
                    print("\033[91mDISASTER WHILE TRYING TO COMPRESS. TELL ADDE\033[0m")
                    print(f"File size: {size}")
                    return 0

    files = [
        file for file in os.listdir(path)
        if file.endswith(".slp")
    ]


    if archives == 1: 
        with zipfile.ZipFile(f"{path}.zip", "w", comp_algo, compresslevel=9) as zipf: # compresslevel does nothing with LZMA
            for file in files:
                zipf.write(f"{path}/{file}", arcname=file)
                if compressed_files is not None:
                    compressed_files.append(file)

    else: 
        parts = __divide_chunks(files, math.ceil(len(files) / archives))
        for i, part in enumerate(parts):
            with zipfile.ZipFile(f"{path} part {i + 1}.zip", "w", comp_algo, compresslevel=9) as zipf: # compresslevel does nothing with LZMA
                for file in part:
                    zipf.write(f"{path}/{file}", arcname=file)
                    if compressed_files is not None:
                        compressed_files.append(file)

    print(f"{path} zipped")
    
    if remove:
        shutil.rmtree(path)

    return archives


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("path")

    args = parser.parse_args()
    path = args.path

    if not os.path.isdir(path):
        print("Invalid path")
        return

    
    print("Compressing...")

    start = time.time()
    compress_folder(path, 0, remove=False)
    end = time.time()

    print(f"Size: {os.path.getsize(f"{path}.zip") / 1024 / 1024}MB")
    print(f"Time: {end - start} seconds")
    os.remove(f"{path}.zip")


if __name__ == "__main__":
    main()
