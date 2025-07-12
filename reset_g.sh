#!/bin/bash

# --- Configuration ---
# The branch you want to completely reset on the remote. Usually 'main' or 'master'.
TARGET_BRANCH="main"

# Your GitHub username
GITHUB_USERNAME="shahar42"

# Your repository name
REPOSITORY_NAME="PROGRAMMING_SUMMARY"

# The path to the file containing the secret that was causing issues (e.g., config/config.env)
# This file will be removed from your local repository and added to .gitignore.
SECRET_FILE="config/config.env"

# --- Safety Checks and Warnings ---

echo "--------------------------------------------------------"
echo "           FULL GIT REPOSITORY RESET SCRIPT"
echo "--------------------------------------------------------"
echo ""
echo "⚠️  EXTREME WARNING: THIS SCRIPT IS HIGHLY DESTRUCTIVE!"
echo "    - It will PERMANENTLY DELETE ALL HISTORY of the '${TARGET_BRANCH}' branch"
echo "      on your remote GitHub repository: https://github.com/${GITHUB_USERNAME}/${REPOSITORY_NAME}.git"
echo "    - All previous commits, branches, and tags on the remote will be GONE."
echo "    - All existing clones of this repository by you or collaborators will become invalid."
echo "    - Collaborators WILL LOSE THEIR WORK if they don't have a backup and will need to re-clone."
echo ""
echo "    PLEASE BACK UP YOUR ENTIRE LOCAL REPOSITORY DIRECTORY NOW!"
echo "    (e.g., by copying the folder to a safe place before running this script)"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null
then
    echo "Error: Git is not installed. Please install Git and try again."
    exit 1
fi

# Get current local branch name
CURRENT_LOCAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_LOCAL_BRANCH" != "$TARGET_BRANCH" ]; then
    echo "Error: You are currently on branch '${CURRENT_LOCAL_BRANCH}'. Please switch to the target branch '${TARGET_BRANCH}' before running this script."
    echo "  git checkout ${TARGET_BRANCH}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: You have uncommitted changes in your working directory."
    echo "Please commit or stash them before running this script, as it will reset your local branch."
    exit 1
fi

# --- git-filter-repo Installation Check and Attempt ---
echo "Checking for git-filter-repo..."
if ! command -v git-filter-repo &> /dev/null
then
    echo "git-filter-repo is not found. Attempting to install using pipx..."

    # Install pipx if not found
    if ! command -v pipx &> /dev/null
    then
        echo "pipx not found. Attempting to install pipx via 'pip install --user'..."
        python3 -m pip install --user pipx
        if [ $? -ne 0 ]; then
            echo "Error: Failed to install pipx using 'pip install --user'."
            echo "It seems your environment is preventing this (e.g., 'externally-managed-environment')."
            echo "Please manually install 'git-filter-repo' into your *active virtual environment* using:"
            echo "  pip install git-filter-repo"
            echo "Then, run this script again."
            exit 1
        fi
        python3 -m pipx ensurepath
        echo "pipx installed via pip --user."
        echo "You might need to open a new terminal or run 'source ~/.bashrc' (or equivalent) if 'pipx' command is not immediately found."
    fi

    # Install git-filter-repo using pipx
    pipx install git-filter-repo
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install git-filter-repo using pipx."
        echo "Please manually install 'git-filter-repo' into your *active virtual environment* using:"
        echo "  pip install git-filter-repo"
        echo "Then, run this script again."
        exit 1
    fi
    echo "git-filter-repo installed via pipx."
fi

# Final check for git-filter-repo after installation attempt
if ! command -v git-filter-repo &> /dev/null
then
    echo "Error: git-filter-repo is still not found after installation attempt."
    echo "Please ensure it's correctly installed and in your system's PATH (or activated virtual environment)."
    exit 1
fi

# Confirm with the user TWICE due to destructive nature
read -p "Are you absolutely sure you want to PERMANENTLY DELETE ALL REMOTE HISTORY for '${TARGET_BRANCH}'? (type 'YES' to confirm): " CONFIRM_1
if [[ ! "$CONFIRM_1" == "YES" ]]
then
    echo "Operation aborted by user."
    exit 0
fi

read -p "LAST CHANCE: This will erase your remote repository. Type 'I UNDERSTAND' to proceed: " CONFIRM_2
if [[ ! "$CONFIRM_2" == "I UNDERSTAND" ]]
then
    echo "Operation aborted by user."
    exit 0
fi

echo "Proceeding with full repository reset..."

# --- Main Logic ---

# Step 1: Remove the problematic file from local and add to .gitignore
echo "Ensuring '${SECRET_FILE}' is removed from local and added to .gitignore..."
if [ -f "$SECRET_FILE" ]; then
    rm "$SECRET_FILE"
    echo "Removed '${SECRET_FILE}' from working directory."
fi

# Add to .gitignore if not already there
if ! grep -q "^${SECRET_FILE}$" .gitignore 2>/dev/null; then
    echo "${SECRET_FILE}" >> .gitignore
    echo "Added '${SECRET_FILE}' to .gitignore."
fi

# Stage changes (removal of secret file, addition to .gitignore)
git add .
git commit -m "Prepare for full repository reset: remove sensitive file and add to .gitignore"

# Step 2: Clean history using git-filter-repo
echo "Cleaning local history using git-filter-repo to remove '${SECRET_FILE}'..."
# git-filter-repo works on the current repository directly.
git filter-repo --path "${SECRET_FILE}" --invert-paths --force
if [ $? -ne 0 ]; then
    echo "Error: git-filter-repo failed during history cleaning. Check the output above."
    exit 1
fi
echo "Local history cleaned of '${SECRET_FILE}'."

# Step 3: Force push the current local branch as the new remote branch
echo "Force pushing current local '${TARGET_BRANCH}' as the new remote history..."
# The --force is critical here to overwrite the remote history.
# We no longer attempt to delete the branch explicitly, as force push will overwrite it.
git push -u origin "${TARGET_BRANCH}" --force
if [ $? -ne 0 ]; then
    echo "Error: Force push failed. Please check your network connection, permissions, or GitHub branch protection rules."
    echo "You may need to temporarily disable branch protection on GitHub if it's enabled."
    exit 1
fi
echo "Remote repository for '${TARGET_BRANCH}' has been reset to your clean local state."

echo ""
echo "--------------------------------------------------------"
echo "           Script Finished Successfully!"
echo "--------------------------------------------------------"
echo ""
echo "IMPORTANT NEXT STEPS:"
echo "1.  Verify on GitHub that your repository history for '${TARGET_BRANCH}' is now clean."
echo "2.  If you had any other local branches, you might need to rebase them onto the new 'main'."
echo "3.  INFORM ALL COLLABORATORS TO DELETE THEIR LOCAL CLONES AND RE-CLONE THE REPOSITORY:"
echo "    git clone https://github.com/${GITHUB_USERNAME}/${REPOSITORY_NAME}.git"
echo "4.  If you need the content of '${SECRET_FILE}' locally (without tracking), create it manually."
echo "    Remember to never commit it again!"
echo ""
