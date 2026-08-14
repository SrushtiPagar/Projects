####################################################################################

## GitHub Automation

####################################################################################

# Used to take information from the command line.

import argparse

# Path helps Python work with files and folders easily.

from pathlib import Path

import json
import shutil
import subprocess
import sys
import os

######################################################################################

parser = argparse.ArgumentParser(
    description="GitHub Automation"
)

# The user must give me a folder location.

parser.add_argument(
    "source_folder",
    help="Source folder"
)

# The user must give a number.

parser.add_argument(
    "count",
    type=int,
    help="Number of files"
)

# The user must give me a GitHub repository.

parser.add_argument(
    "github_repo",
    help="GitHub repository"
)

# The user must give me the destination folder inside the GitHub repository.

parser.add_argument(
    "destination_folder",
    nargs="?",
    default="",
    help="Optional destination folder inside GitHub repository"
)

# This takes what you typed in the command and stores it.

args = parser.parse_args()

# Folder containing this automation script

script_folder = Path(__file__).parent

# Printing the values.

print("Source Folder      :", args.source_folder)
print("Count              :", args.count)
print("GitHub Repo        :", args.github_repo)
print("Destination Folder :", args.destination_folder)

######################################################################################

# Path() converts that text into a Path object.

source_folder = Path(args.source_folder)

# Checking if the folder exists.

if not source_folder.exists():
    print("Source folder does not exist.")
    exit(1)

# Checking if given path is not a folder.

if not source_folder.is_dir():
    print("Invalid source folder.")
    print("The given path is not a folder.")
    exit(1)

######################################################################################

# Check the GitHub repository.

######################################################################################

# Prepare GitHub repository
#
# The user can provide either:
#
# 1. A local Git repository path
# 2. A GitHub repository URL

github_repo_input = args.github_repo

if (
    github_repo_input.startswith("https://")
    or github_repo_input.startswith("http://")
):

    print("GitHub URL detected.")

    # Extract repository name from URL
    repo_name = github_repo_input.rstrip("/").split("/")[-1]

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    # Store cloned repositories inside a local folder
    repository_folder = (
        script_folder / "repositories"
    )

    repository_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    github_repo = repository_folder / repo_name

    # Clone repository if it does not exist
    if not github_repo.exists():

        print(
            "Repository not found locally."
        )

        print(
            "Cloning repository..."
        )

        subprocess.run(
            [
                "git",
                "clone",
                github_repo_input,
                str(github_repo)
            ],
            check=True
        )

        print(
            "Repository cloned successfully."
        )

    else:

        print(
            "Repository already exists locally."
        )

else:

    # Treat argument as a local repository path

    github_repo = Path(
        github_repo_input
    )

# Check repository

if not github_repo.exists():

    print(
        "GitHub repository does not exist."
    )

    exit(1)

git_folder = github_repo / ".git"

if not git_folder.exists():

    print(
        "This is not a Git repository."
    )

    exit(1)

print(
    "Git Repository Path :",
    github_repo
)

######################################################################################

# Destination folder inside the Git repository.
# If no destination is provided, use the repository root.

if args.destination_folder:
    destination_folder = github_repo / args.destination_folder
else:
    destination_folder = github_repo

# Create destination folder if it does not exist.

destination_folder.mkdir(
    parents=True,
    exist_ok=True
)

print("Destination Path   :", destination_folder)

######################################################################################

# Find programming files.

extensions = [
    ".c",
    ".cpp",
    ".java",
    ".py",
    ".js",
    ".html",
    ".css",
    ".php",
    ".rb",
    ".go",
    ".rs",
    ".ts"
]

files = []

for extension in extensions:
    files.extend(source_folder.glob(f"*{extension}"))

# Sort files.

files = sorted(files)

######################################################################################

# uploaded_files.json

# Store JSON files in the same folder as this automation script.


uploaded_file_path = script_folder / "uploaded_files.json"

if not uploaded_file_path.exists():

    data = {
        "uploaded_files": []
    }

    with open(uploaded_file_path, "w") as file:
        json.dump(data, file, indent=4)

# Read uploaded_files.json

with open(uploaded_file_path, "r") as file:
    uploaded_data = json.load(file)

uploaded_files = uploaded_data["uploaded_files"]

print("Uploaded files:", uploaded_files)
print("Updating:", uploaded_file_path)

######################################################################################

# Get actual files from the Git repository.

result = subprocess.run(
    ["git", "ls-files"],
    cwd=github_repo,
    capture_output=True,
    text=True,
    check=True
)

# Store complete Git paths.

github_files = result.stdout.splitlines()

print("Files currently in GitHub repository:")

for file in github_files:
    print(file)

######################################################################################

# Update github_files.json

github_file_path = script_folder / "github_files.json"

github_data = {
    "github_files": github_files
}

with open(github_file_path, "w") as file:
    json.dump(github_data, file, indent=4)

######################################################################################

# Find files that are not uploaded yet
# and are not already present in the destination folder.

new_files = []

for file in files:

    destination = destination_folder / file.name

    relative_path = destination.relative_to(github_repo)

    github_path = str(relative_path).replace("\\", "/")

    if file.name in uploaded_files:
        continue

    if github_path in github_files:
        continue

    new_files.append(file)

# Select required number of new files.

selected_files = new_files[:args.count]

# Display selected files.

print("\nSelected files:")

for file in selected_files:
    print(file.name)

######################################################################################

# Process one file at a time.

for current_file in selected_files:

    print("\nProcessing:", current_file.name)

    try:

        # --------------------------------------------------
        # Copy file to destination folder
        # --------------------------------------------------

        destination = destination_folder / current_file.name

        shutil.copy2(
            current_file,
            destination
        )

        print("Copied to:", destination)

        # --------------------------------------------------
        # Get relative Git path
        # --------------------------------------------------

        relative_file = destination.relative_to(github_repo)

        relative_file = str(relative_file).replace("\\", "/")

        print("Git path:", relative_file)

        # --------------------------------------------------
        # Check for latest changes from GitHub
        # --------------------------------------------------

        print("Checking GitHub for latest changes...")

        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=github_repo,
            check=True
        )

        print("Repository synchronized.")

        # --------------------------------------------------
        # Git add
        # --------------------------------------------------

        subprocess.run(
            ["git", "add", relative_file],
            cwd=github_repo,
            check=True
        )

        print("File staged.")

        # --------------------------------------------------
        # Git commit
        # --------------------------------------------------

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Add {current_file.name}"
            ],
            cwd=github_repo,
            check=True
        )

        print("Commit created.")

        # --------------------------------------------------
        # Git push
        # --------------------------------------------------

        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=github_repo,
            check=True
        )

        print("Pushed to GitHub:", current_file.name)

        # --------------------------------------------------
        # Update uploaded_files.json
        # ONLY after push succeeds
        # --------------------------------------------------

        uploaded_files.append(current_file.name)

        uploaded_data["uploaded_files"] = uploaded_files

        with open(uploaded_file_path, "w") as file:
            json.dump(
                uploaded_data,
                file,
                indent=4
            )

        print("Updated uploaded_files.json")

        # --------------------------------------------------
        # Refresh GitHub repository files
        # --------------------------------------------------

        result = subprocess.run(
            ["git", "ls-files"],
            cwd=github_repo,
            capture_output=True,
            text=True,
            check=True
        )

        github_files = result.stdout.splitlines()

        # --------------------------------------------------
        # Update github_files.json
        # --------------------------------------------------

        github_data["github_files"] = github_files

        with open(github_file_path, "w") as file:
            json.dump(
                github_data,
                file,
                indent=4
            )

        print("Updated github_files.json")

        print(
            "Successfully processed:",
            current_file.name
        )

    except subprocess.CalledProcessError as error:
        print()
        print("GitHub Automation failed.")
        print("Reason:", error)

        print("JSON files were NOT updated.")

        continue

    except Exception as error:

        print(
            "\nError processing:",
            current_file.name
        )

        print("Reason:", error)

        print("JSON files were NOT updated.")

        continue

######################################################################################     