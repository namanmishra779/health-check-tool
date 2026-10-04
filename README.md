# Health Check CLI

A cross-platform Python CLI for disk-capacity reporting and cautious cleanup of aged application logs. It uses only the Python standard library, previews by default, and deletes files only when explicitly invoked with `--apply`.

## Project highlights

- Reports used space, free GiB, and `OK`/`WARN` status for a selected filesystem.
- Filters old, top-level `.log` files by modification time; unrelated and recent files are left alone.
- Continues past per-file operating-system errors instead of aborting the whole cleanup.
- Includes unit tests and a GitHub Actions matrix for Windows and Ubuntu on Python 3.10 and 3.12.

This is a small operations-tooling portfolio project: the emphasis is safe defaults, testable functions, and repeatable cross-platform checks.

## 1. Open the project folder

In the VS Code terminal (PowerShell), from the current `HealthCheck` workspace:

```powershell
Set-Location .\health_check_project
```

Check that the project files are here:

```powershell
Get-ChildItem
```

## 2. Create and use a virtual environment

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

When activation works, the prompt usually starts with `(.venv)`. If PowerShell blocks activation, skip activation and run the interpreter directly as shown below. There are no third-party packages to install, so `requirements.txt` is intentionally empty.

## 3. Prepare old sample logs

The project includes `app.log`, `error.log`, and `notes.txt`. Backdate just the two log files so they qualify as older than seven days:

```powershell
(Get-Item .\logs\app.log).LastWriteTime = (Get-Date).AddDays(-10)
(Get-Item .\logs\error.log).LastWriteTime = (Get-Date).AddDays(-10)
Get-ChildItem .\logs | Select-Object Name, LastWriteTime
```

`notes.txt` is not a `.log`, so the cleaner should leave it alone.

## 4. Preview first

With the virtual environment active:

```powershell
python .\health_check.py --logs .\logs --days 7 --dry-run
```

Or without activating it:

```powershell
.\.venv\Scripts\python.exe .\health_check.py --logs .\logs --days 7 --dry-run
```

You should see disk details and a `would delete` list containing `app.log` and `error.log`. Your disk numbers and path will differ. Confirm all three files are still present:

```powershell
Get-ChildItem .\logs
```

## 5. Apply cleanup only after checking the preview

When the preview is correct, explicitly opt in to deletion:

```powershell
python .\health_check.py --logs .\logs --days 7 --apply
```

The output should say `deleted` and list the two old logs. `notes.txt` should remain. Running the same command again should report `deleted: []`.

## 6. Explore the options

```powershell
python .\health_check.py --help
python .\health_check.py --warn 5
python .\health_check.py --logs .\logs --days 0 --dry-run
```

`--warn 5` sets a low disk warning threshold. `--days 0 --dry-run` previews any `.log` file in the target directory without deleting it. The cleaner checks files directly inside the selected directory, not nested folders.

## Run the test suite

No test or runtime packages need to be installed. From the project root, run:

```powershell
python -m unittest discover --start-directory tests --verbose
```

The tests cover disk threshold behavior, preview safety, selective deletion, and per-file error handling. GitHub Actions runs the same suite on pushes and pull requests.

## How it works

- `check_disk()` returns a dictionary, so its result can be inspected or tested.
- `clean_logs()` checks each matching file separately and skips a file if the operating system reports an `OSError`.
- `--dry-run` is the default; `--apply` is the only option that enables deletion.
- `--mount` defaults to the current Windows drive root. Pass another path to check a different filesystem.
- Cleanup is non-recursive: it examines `.log` files directly inside the directory given to `--logs`.

## Scheduling

On Windows, create a task in Task Scheduler that runs the project's `.venv\Scripts\python.exe` with the full path to `health_check.py` and the required `--logs` path. Test the exact command manually first, and consider capturing output to a log file. For cron, run the project under Linux or WSL and use absolute paths to both the virtual-environment Python and script; cron is not available in ordinary PowerShell.

## Troubleshooting

- `python` is not recognized: install Python 3 and reopen the terminal, or use the Python launcher command `py` instead.
- No files are listed: check the `--logs` path and the file dates; use the backdating commands above.
- Permission error: the script prints `skip ...` for that file and continues.
- Nothing should be deleted during preview. Do not add `--apply` until you have checked the candidate list.
