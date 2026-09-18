# Parallel Keyword Search

A Python program that searches for specified keywords across multiple text files using two parallel approaches:

- **Multi-threading** (`threading` module)
- **Multi-processing** (`multiprocessing` module)

The program demonstrates practical differences between threads and processes, measures execution time of both implementations, and returns results in a clean dictionary format.

---

## Features

- Parallel processing of text files using threads and processes
- Even distribution of files across workers
- Safe data exchange via `threading.Lock` (threads) and `multiprocessing.Queue` (processes)
- Execution time measurement for both implementations
- Robust error handling for file system operations
- Returns results as: `{keyword: [list of file paths]}`
- Configurable number of workers and keywords

---

## Requirements

- Python 3.8+
- No external dependencies (uses only the standard library)

---

## Project Structure

```
.
├── parallel_keyword_search.py   # Main program
├── text_files/                  # Directory with sample .txt files
│   ├── file1.txt
│   ├── file2.txt
│   ├── file3.txt
│   ├── file4.txt
│   └── file5.txt
└── README.md
```

---

## Usage

1. Place your `.txt` files into the `text_files/` directory (or change the path in the configuration section).

2. Run the program:

```bash
python parallel_keyword_search.py
```

The program will:

1. Scan the `text_files/` directory
2. Run the multi-threaded search and measure its time
3. Run the multi-process search and measure its time
4. Print detailed results and a performance summary

---

## Configuration

You can easily change the following parameters at the top of `parallel_keyword_search.py`:

```python
KEYWORDS = [
    "python", "thread", "process", "parallel",
    "queue", "multiprocessing", "threading"
]
FILES_DIR = Path(__file__).parent / "text_files"
NUM_WORKERS = 3          # Number of threads / processes
```

---

## How It Works

### Multi-threading version
- Files are split into chunks and assigned to separate threads
- Threads share memory, so results are collected into a common dictionary protected by a `Lock`
- Suitable for I/O-bound tasks

### Multi-processing version
- Files are split into chunks and assigned to separate processes
- Processes do not share memory — results are sent back via a `multiprocessing.Queue`
- Suitable for CPU-bound tasks and bypasses the Global Interpreter Lock (GIL)

---

## Output Format

Both implementations return a dictionary of the following structure:

```python
{
    "keyword1": ["path/to/file1.txt", "path/to/file3.txt"],
    "keyword2": ["path/to/file2.txt"],
    ...
}
```

Example console output:

```
RESULTS: MULTI-THREADED VERSION (threading)
======================================================================
Execution time: 0.0031 seconds
----------------------------------------------------------------------

🔑 'process' found in 3 file(s):
   • /path/to/text_files/file1.txt
   • /path/to/text_files/file3.txt
   • /path/to/text_files/file4.txt
...
```

---

## Error Handling

The program gracefully handles common file system issues:

- Missing directory
- Permission errors
- Non-existent files
- Attempt to open a directory as a file
- Encoding problems (uses `errors="ignore"`)

---

## License

This project is open source and available under the MIT License.
