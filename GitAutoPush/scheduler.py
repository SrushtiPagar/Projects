####################################################################################
# GitHub Automation Scheduler
####################################################################################

import argparse
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

####################################################################################
# Command-line arguments
####################################################################################

parser = argparse.ArgumentParser(
    description="GitHub Automation Scheduler"
)

parser.add_argument(
    "source_folder",
    help="Source folder"
)

parser.add_argument(
    "count",
    type=int,
    help="Number of files"
)

parser.add_argument(
    "github_repo",
    help="GitHub repository"
)

parser.add_argument(
    "destination_folder",
    nargs="?",
    default="",
    help="Optional destination folder inside GitHub repository"
)

parser.add_argument(
    "--time",
    required=True,
    help="Daily execution time in HH:MM format"
)

args = parser.parse_args()

####################################################################################
# Validate time
####################################################################################

try:

    schedule_time = datetime.strptime(
        args.time,
        "%H:%M"
    ).time()

except ValueError:

    print("Invalid time format.")
    print("Please use HH:MM format.")
    print("Example: --time 16:30")

    exit()

####################################################################################
# Locate automation script
####################################################################################

automation_script = (
    Path(__file__).parent /
    "Automation_github.py"
)

if not automation_script.exists():

    print(
        "Automation_github.py not found."
    )

    exit()

####################################################################################
# Display configuration
####################################################################################

print()
print("==============================================")
print("       GitHub Automation Scheduler")
print("==============================================")

print(
    "Source Folder      :",
    args.source_folder
)

print(
    "Count              :",
    args.count
)

print(
    "GitHub Repository  :",
    args.github_repo
)

if args.destination_folder:

    print(
        "Destination Folder :",
        args.destination_folder
    )

else:

    print(
        "Destination Folder :",
        "Repository Root"
    )

print(
    "Daily Run Time     :",
    args.time
)

print("==============================================")

####################################################################################
# Continuous daily scheduler
####################################################################################

while True:

    now = datetime.now()

    ############################################################################
    # Create today's scheduled datetime
    ############################################################################

    next_run = datetime.combine(
        now.date(),
        schedule_time
    )

    ############################################################################
    # If today's scheduled time has already passed,
    # schedule for tomorrow.
    ############################################################################

    if next_run <= now:

        next_run = next_run + timedelta(days=1)

    ############################################################################
    # Display waiting information
    ############################################################################

    waiting_seconds = (
        next_run - now
    ).total_seconds()

    print()
    print("----------------------------------------------")

    print(
        "Current Time :",
        now.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "Next Run     :",
        next_run.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "Waiting      :",
        int(waiting_seconds),
        "seconds"
    )

    print(
        "Scheduler is waiting..."
    )

    print("----------------------------------------------")

    ############################################################################
    # Wait until scheduled time
    #
    # Instead of sleeping for many hours at once,
    # check the time every 30 seconds.
    ############################################################################

    while True:

        now = datetime.now()

        if now >= next_run:

            break

        remaining_seconds = (
            next_run - now
        ).total_seconds()

        sleep_time = min(
            30,
            remaining_seconds
        )

        time.sleep(sleep_time)

    ############################################################################
    # Scheduled time reached
    ############################################################################

    print()
    print("==============================================")
    print("Scheduled time reached!")
    print("Starting GitHub Automation...")
    print("==============================================")

    try:

        ############################################################################
        # Build automation command
        ############################################################################

        command = [
            sys.executable,
            str(automation_script),
            args.source_folder,
            str(args.count),
            args.github_repo
        ]

        ############################################################################
        # Add destination folder only if provided
        ############################################################################

        if args.destination_folder:

            command.append(
                args.destination_folder
            )

        ############################################################################
        # Run GitHub automation
        ############################################################################

        subprocess.run(
            command,
            check=True
        )

        print()
        print(
            "GitHub Automation completed successfully."
        )

    except subprocess.CalledProcessError as error:

        print()
        print(
            "GitHub Automation failed."
        )

        print(
            "Reason:",
            error
        )

    except Exception as error:

        print()
        print(
            "Unexpected error."
        )

        print(
            "Reason:",
            error
        )

    ############################################################################
    # Today's automation is finished
    #
    # The outer while loop now starts again and schedules tomorrow.
    ############################################################################

    print()
    print(
        "Today's automation is finished."
    )

    print(
        "Scheduler will continue running for tomorrow."
    )

    print(
        "=============================================="
    )
