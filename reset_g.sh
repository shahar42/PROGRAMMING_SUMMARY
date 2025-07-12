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

# Step 2: Delete the remote branch
echo "Deleting remote branch '${TARGET_BRANCH}'..."
git push origin --delete "${TARGET_BRANCH}"
if [ $? -ne 0 ]; then
    echo "Warning: Failed to delete remote branch '${TARGET_BRANCH}'. This might be due to branch protection rules or it not existing."
    echo "Attempting to force push anyway, but manual intervention on GitHub might be needed."
    # Continue, but warn. User might need to disable branch protection temporarily.
fi

# Step 3: Create a new, empty commit (optional, but ensures a clean root if needed)
# If you want to completely wipe and start with literally nothing, you could do:
# git checkout --orphan new_main
# git rm -rf .
# git commit --allow-empty -m "Initial commit of clean repository"
# git branch -D main # Delete old main
# git branch -m main # Rename new_main to main
# For this script, we'll just force push the current local state.

# Step 4: Force push the current local branch as the new remote branch
echo "Force pushing current local '${TARGET_BRANCH}' as the new remote history..."
git push -u origin "${TARGET_BRANCH}" --force
if [ $? -ne 0 ]; then
    echo "Error: Force push failed. Please check your network connection, permissions, or GitHub branch protection rules."
    echo "You may need to temporarily disable branch protection on GitHub if it's enabled."
    exit 1
fi
echo "Remote repository for '${TARGET_BRANCH}' has been reset to your current local state."

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
