# GitHub Automation

A reusable Python automation tool that uploads programming files from a local folder to a Git repository and pushes them to GitHub — automatically, on a schedule, with no hardcoded paths.

The project supports:

- Uploading a configurable number of files at a time
- Local Git repositories **or** GitHub repository URLs (auto-clone)
- Custom destination folders inside the repository
- Automatic `git pull`, `add`, `commit`, and `push`
- Tracking of already-uploaded files (no duplicates)
- Daily scheduled automation
- Full command-line configuration — no editing the source code per project

---

## Project Structure

```
Github_Automation/
│
├── Automation_github10.py   # Main automation script
├── scheduler.py              # Daily scheduler wrapper
│
├── uploaded_files.json       # Tracks files already uploaded
├── github_files.json         # Snapshot of files currently in the repo
│
├── README.md
└── repositories/             # Auto-created when a GitHub URL is cloned
```

---

## Requirements

- **Python 3.x** — check with `python --version`
- **Git** — check with `git --version`, must be available on the command line

No external Python packages are required — the project only uses the standard library (`argparse`, `pathlib`, `json`, `shutil`, `subprocess`, `sys`, `os`).

---

## How It Works

```
Source Folder
     │
     ▼
Find programming files (.py, .java, .c, .cpp, .js, .html, .css, .php, .rb, .go, .rs, .ts)
     │
     ▼
Skip files already in uploaded_files.json or already present in the repo
     │
     ▼
Select up to N new files
     │
     ▼
For each file: copy → git pull --rebase → git add → git commit → git push
     │
     ▼
Update uploaded_files.json and github_files.json (only after a successful push)
```

If a file fails to push, it is skipped and the JSON tracking files are **not** updated for that file — so it will be retried on the next run.

---

## Usage

### Command syntax

```bash
python Automation_github10.py SOURCE_FOLDER COUNT GITHUB_REPO [DESTINATION_FOLDER]
```

| Argument | Required | Description |
|---|---|---|
| `SOURCE_FOLDER` | Yes | Folder containing the files to upload |
| `COUNT` | Yes | Number of new files to upload in this run |
| `GITHUB_REPO` | Yes | Local Git repository path **or** GitHub repository URL |
| `DESTINATION_FOLDER` | No | Folder inside the repo to copy files into (defaults to repo root) |

### Example — local Git repository

```bash
python Automation_github10.py "C:\Users\User\Desktop\Python\Programs" 3 "C:\Users\User\Programming" "Python_Programming\Practice"
```

### Example — GitHub repository URL

```bash
python Automation_github10.py "C:\Users\User\Desktop\Python\Programs" 3 "https://github.com/username/repository" "Python_Programming\Practice"
```

When a URL is provided, the repository is cloned automatically into `repositories/<repo_name>` (only if it isn't already cloned there).

### Example — no destination folder (uploads to repo root)

```bash
python Automation_github10.py "C:\Programs" 2 "C:\MyRepository"
```

---

## Daily Scheduler

`scheduler.py` runs the automation automatically every day at a fixed time.

```bash
python scheduler.py "C:\Users\User\Desktop\Python\Programs" 2 "https://github.com/username/repository" "Python_Programming/Practice" --time 18:30
```

It waits until the given time, runs `Automation_github10.py` with the same arguments, then loops and waits for the next day — indefinitely.

---

## Tracking Files

**`uploaded_files.json`** — names of files already uploaded successfully:

```json
{
    "uploaded_files": [
        "Program1.py",
        "Program2.py"
    ]
}
```

**`github_files.json`** — snapshot of file paths currently tracked by Git in the repo (refreshed via `git ls-files` before and after each run):

```json
{
    "github_files": [
        "README.md",
        "Python_Programming/Practice/Program1.py"
    ]
}
```

---

## Notes

- `repositories/` is created only when a GitHub URL is passed; it holds runtime clones and generally shouldn't be committed.
- Both `uploaded_files.json` and `github_files.json` are stored next to the script, not inside the target repository.
- The script currently pushes to the `main` branch — adjust the `git pull` / `git push` calls in `Automation_github10.py` if your repo uses a different default branch.

---

## How to run

python scheduler.py "SOURCE_FOLDER" COUNT "GITHUB_REPO" "DESTINATION_FOLDER" --time HH:MM

| Argument                                        | Meaning                           |
| ----------------------------------------------- | --------------------------------- |
| `scheduler.py`                                  | Scheduler program                 |
| `"C:\...\Automations"`                          | Folder containing files to upload |
| `1`                                             | Upload maximum 1 file per day     |
| `"https://github.com/SrushtiPagar/Programming"` | GitHub repository                 |
| `"Python_Programming/Practice/Automation"`      | Destination folder                |
| `--time 18:30`                                  | Run every day at 6:30 PM          |

## You'll see something like:

==============================================
       GitHub Automation Scheduler
==============================================


Source Folder      : C:\...
Count              : 1
GitHub Repository  : https://github.com/...
Destination Folder : Python_Programming/Practice/Automation
Daily Run Time     : 18:30
==============================================


Current Time : 2026-08-14 18:20:15
Next Run     : 2026-08-14 18:30:00
Waiting      : 585 seconds
Scheduler is waiting...
