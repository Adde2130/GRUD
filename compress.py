import zipfile
import math
import os
import shutil
import argparse
import time
import uuid

'''Rough estimations for SLP file compression'''

LZMA_RATIO = 0.13963562606

ZLIB_RATIO = 0.23253719347

# NOTE: This is BLAZINGLY fast, and is prefferable if size isn't an issue
BZIP2_RATIO = 0.21835793841

BASE_MARGIN = 0.75

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

    margin = min(BASE_MARGIN + ( size_limit / 1024 / 1024 / 2 / 100 ), 1)

    if size * BZIP2_RATIO < size_limit * margin: 
        comp_algo = zipfile.ZIP_BZIP2
        print(f"Zipping {path} with BZIP2")
    else:
        comp_algo = zipfile.ZIP_LZMA
        print(f"Zipping {path} with LZMA")

        if size * LZMA_RATIO > size_limit * margin:
            print(f"Zipping {path} in multiple parts")
            while size * LZMA_RATIO / archives > size_limit * margin:
                archives += 1

                if size * BZIP2_RATIO / archives > size_limit * margin:
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

def compress_new(path: str, size_limit: int, compressed_files=None, remove=False, verbose=False):
    if size_limit == 0:
        size_limit = 0xFFFFFFFF # 4GB

    path = os.path.abspath(path)

    files = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if f.endswith(".slp")
    ]


    algo = zipfile.ZIP_BZIP2
    compression_ratio = 1 / 4

    folder_size = os.path.getsize(path)

    # If we have to create more than one archive, just switch the
    # compression algorithm since we don't want too many parts
    if folder_size > size_limit * 4.5:
        algo = zipfile.ZIP_LZMA
        compression_ratio = 1 / 6


    archive_name = f"{path} part 1.zip"
    archive_num = 1
    archive = zipfile.ZipFile(archive_name, "w", algo, compresslevel=9) 

    archives = [archive_name]

    for file in files:
        file_size = os.path.getsize(file)
        archive_size = os.path.getsize(archive_name)

        print(
            f"ARCHIVE SIZE: \033[96;1m{round(archive_size / 1024 / 1024, 2)}\033[0mMB, "
            f"FILE SIZE: \033[93;1m{round(file_size / 1024 / 1024, 2)}\033[0mMB",
            f"COMPRESSED FILE SIZE: \033[91;1m{round(file_size / 1024 / 1024 * compression_ratio, 2)}\033[0mMB"
        )

        
        if archive_size + file_size * compression_ratio > size_limit:
            if verbose:
                print(f"\033[94mCreating new archive! {archive_num}\033[39m")
            archive.close()
            
            archive_num += 1

            archive_name = f"{path} part {archive_num}.zip"
            archive = zipfile.ZipFile(archive_name, "w", algo, compresslevel=9) 
            archives.append(archive_name)

        archive.write(file)
        if compressed_files is not None:
            compressed_files.append(file)

    archive.close()

    if len(archives) == 1:
        archive_name = f"{path}.zip"
        old_archive_name = archives[0]
        archives[0] = archive_name
        if os.path.exists(archive_name):
            new_name = f"{uuid.uuid4()}.zip"
            print(f"Filename already exists!!! Big whoopsie. Renaming it to {new_name} instead.")
            os.rename(old_archive_name, new_name)
        else:
            os.rename(old_archive_name, archive_name)

    if remove:
        # I know ignoring is bad but testing multiprocessing is a pain,
        # and SU replays have already been fucked multiple times due to
        # this rmtree function.
        shutil.rmtree(path, ignore_errors=True)

    return archives

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("path")

    args = parser.parse_args()
    path = args.path

    if not os.path.isdir(path):
        print("Invalid path")
        return

    print(compress_new(path, 50 * 1024 * 1024, remove=False, verbose=True))

if __name__ == "__main__":
    main()
