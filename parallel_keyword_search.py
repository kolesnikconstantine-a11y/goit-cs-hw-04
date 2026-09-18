#!/usr/bin/env python3
"""
Parallel keyword search in text files.
Single file with two implementations: threading and multiprocessing.

Returns a dictionary: {keyword: [list of file paths where it was found]}
Measures and prints the execution time of each version.
"""

import os
import time
import threading
import multiprocessing as mp
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set


# ========================== CONFIGURATION ==========================
KEYWORDS = [
    "python", "thread", "process", "parallel",
    "queue", "multiprocessing", "threading"
]
FILES_DIR = Path(__file__).parent / "text_files"
NUM_WORKERS = 4          # Number of threads / processes


# ========================== HELPER FUNCTIONS ==========================

def get_text_files(directory: Path) -> List[Path]:
    """Return a list of all .txt files in the directory with error handling."""
    try:
        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        files = sorted(directory.glob("*.txt"))
        if not files:
            print(f"[Warning] No .txt files found in directory {directory}")
        return files
    except Exception as e:
        print(f"[Error] Failed to get file list: {e}")
        return []


def find_keywords_in_file(filepath: Path, keywords: List[str]) -> Set[str]:
    """
    Search for keywords in a file.
    Returns a set of keywords that were found at least once.
    """
    found = set()
    keywords_lower = {kw.lower(): kw for kw in keywords}  # lower -> original

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_lower = line.lower()
                for kw_lower, kw_original in keywords_lower.items():
                    if kw_lower in line_lower:
                        found.add(kw_original)
    except FileNotFoundError:
        print(f"[Error] File not found: {filepath}")
    except PermissionError:
        print(f"[Error] Permission denied: {filepath}")
    except IsADirectoryError:
        print(f"[Error] Expected a file, got a directory: {filepath}")
    except Exception as e:
        print(f"[Error] Failed to read {filepath}: {type(e).__name__}: {e}")

    return found


def split_list(lst: List, n: int) -> List[List]:
    """Evenly split a list into n parts."""
    if n <= 0:
        return [lst]
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


# ========================== THREADING VERSION ==========================

def _thread_worker(file_list: List[Path], keywords: List[str],
                   results: Dict[str, Set[str]], lock: threading.Lock):
    """Worker function for a thread."""
    local_found = defaultdict(set)  # keyword -> set of file paths

    for filepath in file_list:
        found_kws = find_keywords_in_file(filepath, keywords)
        for kw in found_kws:
            local_found[kw].add(str(filepath))

    # Safely update the shared dictionary
    with lock:
        for kw, paths in local_found.items():
            if kw not in results:
                results[kw] = set()
            results[kw].update(paths)


def search_with_threading(files: List[Path], keywords: List[str],
                          num_workers: int = NUM_WORKERS) -> Dict[str, List[str]]:
    """
    Multi-threaded search.
    Returns: {keyword: [list of file paths]}
    """
    if not files:
        return {}

    results: Dict[str, Set[str]] = {}
    lock = threading.Lock()
    chunks = split_list(files, num_workers)
    threads = []

    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        t = threading.Thread(
            target=_thread_worker,
            args=(chunk, keywords, results, lock),
            name=f"Thread-{i+1}"
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Convert set -> sorted list
    return {kw: sorted(list(paths)) for kw, paths in sorted(results.items())}


# ========================== MULTIPROCESSING VERSION ==========================

def _process_worker(file_list: List[str], keywords: List[str],
                    result_queue: mp.Queue):
    """Worker function for a process."""
    local_found = defaultdict(set)  # keyword -> set of file paths

    for filepath_str in file_list:
        filepath = Path(filepath_str)
        found_kws = find_keywords_in_file(filepath, keywords)
        for kw in found_kws:
            local_found[kw].add(filepath_str)

    # Send the result to the queue
    result_queue.put(dict(local_found))


def search_with_multiprocessing(files: List[Path], keywords: List[str],
                                num_workers: int = NUM_WORKERS) -> Dict[str, List[str]]:
    """
    Multi-process search.
    Returns: {keyword: [list of file paths]}
    """
    if not files:
        return {}

    # Pass strings (Path objects are not always easily serializable)
    file_strs = [str(f) for f in files]
    chunks = split_list(file_strs, num_workers)

    result_queue = mp.Queue()
    processes = []

    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        p = mp.Process(
            target=_process_worker,
            args=(chunk, keywords, result_queue),
            name=f"Process-{i+1}"
        )
        processes.append(p)
        p.start()

    # Collect results from the queue
    combined: Dict[str, Set[str]] = defaultdict(set)
    for _ in processes:
        partial = result_queue.get()
        for kw, paths in partial.items():
            combined[kw].update(paths)

    for p in processes:
        p.join()

    return {kw: sorted(list(paths)) for kw, paths in sorted(combined.items())}


# ========================== MAIN FUNCTION ==========================

def print_results(title: str, results: Dict[str, List[str]], elapsed: float):
    """Pretty-print the search results."""
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)
    print(f"Execution time: {elapsed:.4f} seconds")
    print("-" * 70)

    if not results:
        print("No keywords found.")
        return

    for keyword, paths in results.items():
        print(f"\n🔑 '{keyword}' found in {len(paths)} file(s):")
        for path in paths:
            print(f"   • {path}")


def main():
    print("=" * 70)
    print("PARALLEL KEYWORD SEARCH IN TEXT FILES")
    print("=" * 70)
    print(f"Directory:      {FILES_DIR}")
    print(f"Keywords:       {KEYWORDS}")
    print(f"Number of workers: {NUM_WORKERS}")

    files = get_text_files(FILES_DIR)
    if not files:
        print("\nNo files to process. Exiting.")
        return

    print(f"Found files: {len(files)}")
    for f in files:
        print(f"   • {f.name}")

    # ---------- THREADING ----------
    start = time.perf_counter()
    threaded_results = search_with_threading(files, KEYWORDS, NUM_WORKERS)
    elapsed_threaded = time.perf_counter() - start

    print_results(
        "RESULTS: MULTI-THREADED VERSION (threading)",
        threaded_results,
        elapsed_threaded
    )

    # ---------- MULTIPROCESSING ----------
    start = time.perf_counter()
    mp_results = search_with_multiprocessing(files, KEYWORDS, NUM_WORKERS)
    elapsed_mp = time.perf_counter() - start

    print_results(
        "RESULTS: MULTI-PROCESS VERSION (multiprocessing)",
        mp_results,
        elapsed_mp
    )

    # ---------- SUMMARY ----------
    print("\n" + "=" * 70)
    print("EXECUTION TIME SUMMARY")
    print("=" * 70)
    print(f"Threading:       {elapsed_threaded:.4f} s")
    print(f"Multiprocessing: {elapsed_mp:.4f} s")
    if elapsed_threaded > 0:
        ratio = elapsed_mp / elapsed_threaded
        print(f"Ratio (mp / threaded): {ratio:.2f}x")
    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    # Recommended for multiprocessing (especially on Windows)
    mp.set_start_method("spawn", force=True)
    main()
