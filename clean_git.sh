#!/bin/bash

# --- Configuration ---
# The path to the file containing the secret.
# IMPORTANT: Ensure this path is correct relative to your repository root.
SECRET_FILE="config/config.env"

# The branch you want to clean. Usually 'main' or 'master'.
TARGET_BRANCH="main"

# Your GitHub username (used for cloning)
GITHUB_USERNAME="shahar42"

# Your repository name (used for cloning)
REPOSITORY_NAME="PROGRAMMING_SUMMARY"

# --- Safety Checks and Warnings ---

echo "--------------------------------------------------------"
echo "           Comprehensive Git History Cleaner Script"
echo "--------------------------------------------------------"
echo ""
echo "⚠️  WARNING: This script will rewrite your Git history!"
echo "    - It will permanently remove '${SECRET_FILE}' from ALL commits."
echo "    - All existing clones of this repository will become outdated."
echo "    - Collaborators will need to re-clone or hard reset their repos."
echo ""
echo "    PLEASE BACK UP YOUR ORIGINAL REPOSITORY BEFORE PROCEEDING!"
echo "    (e.g., by copying the entire directory to a safe place)"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null
then
    echo "Error: Git is not installed. Please install Git and try again."
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
        echo "pipx not found. Attempting to install pipx via apt (if available)..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y pipx
            if [ $? -eq 0 ]; then
                echo "pipx installed via apt."
                python3 -m pipx ensurepath
            else
                echo "Failed to install pipx via apt. Falling back to pip install --user..."
                python3 -m pip install --user pipx
                if [ $? -ne 0 ]; then
                    echo "Error: Failed to install pipx using pip install --user."
                    echo "You might need to resolve 'externally-managed-environment' issues manually."
                    echo "Consider using 'python3 -m venv' to create a virtual environment and install pipx there."
                    exit 1
                fi
                python3 -m pipx ensurepath
                echo "pipx installed via pip --user."
            fi
        else
            echo "apt not found. Attempting to install pipx via pip install --user..."
            python3 -m pip install --user pipx
            if [ $? -ne 0 ]; then
                echo "Error: Failed to install pipx using pip install --user."
                echo "You might need to resolve 'externally-managed-environment' issues manually."
                echo "Consider using 'python3 -m venv' to create a virtual environment and install pipx there."
                exit 1
            fi
            python3 -m pipx ensurepath
            echo "pipx installed via pip --user."
        fi
        # Re-source shell to update PATH, or instruct user to do so
        # This is tricky in a script. We'll rely on pipx ensurepath making it available.
        # For a new shell, user would need to re-source their shell config.
        echo "You might need to open a new terminal or run 'source ~/.bashrc' (or equivalent) if 'pipx' command is not immediately found."
    fi

    # Install git-filter-repo using pipx
    pipx install git-filter-repo
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install git-filter-repo using pipx."
        echo "Please try installing it manually using one of the methods described in the previous script."
        exit 1
    fi
    echo "git-filter-repo installed via pipx."
fi

# Final check for git-filter-repo after installation attempt
if ! command -v git-filter-repo &> /dev/null
then
    echo "Error: git-filter-repo is still not found after installation attempt."
    echo "Please ensure it's correctly installed and in your system's PATH."
    exit 1
fi

# Confirm with the user
read -p "Do you understand the risks and wish to continue? (yes/no): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]
then
    echo "Operation aborted by user."
    exit 0
fi

# --- Main Logic ---

# Create a temporary directory for cloning and cleaning
TEMP_DIR=$(mktemp -d -t git-clean-XXXXXXXXXX)
if [ $? -ne 0 ]; then
    echo "Error: Could not create temporary directory."
    exit 1
fi
echo "Created temporary directory: ${TEMP_DIR}"

# Clone the repository into the temporary directory
echo "Cloning repository into temporary directory..."
git clone "https://github.com/${GITHUB_USERNAME}/${REPOSITORY_NAME}.git" "${TEMP_DIR}/repo_to_clean"
if [ $? -ne 0 ]; then
    echo "Error: Failed to clone repository."
    rm -rf "${TEMP_DIR}"
    exit 1
fi
echo "Repository cloned."

# Change into the cloned repository directory
cd "${TEMP_DIR}/repo_to_clean" || { echo "Error: Could not change directory to cloned repo."; rm -rf "${TEMP_DIR}"; exit 1; }

# Ensure we are on the target branch
echo "Checking out target branch: ${TARGET_BRANCH}"
git checkout "${TARGET_BRANCH}"
if [ $? -ne 0 ]; then
    echo "Error: Failed to checkout branch ${TARGET_BRANCH}. Make sure the branch exists."
    cd - > /dev/null # Go back to original directory
    rm -rf "${TEMP_DIR}"
    exit 1
fi

echo "Running git-filter-repo to remove '${SECRET_FILE}' from all history..."
# The --path-glob option allows for wildcards if needed, but for a specific file, direct path is fine.
# --invert-paths means "keep everything EXCEPT this path".
# --force is needed because git-filter-repo might complain about existing history.
git filter-repo --path "${SECRET_FILE}" --invert-paths --force
if [ $? -ne 0 ]; then
    echo "Error: git-filter-repo failed. Check the output above for details."
    cd - > /dev/null
    rm -rf "${TEMP_DIR}"
    exit 1
fi
echo "History rewritten locally."

# Add the file to .gitignore to prevent future accidental commits
echo "${SECRET_FILE}" >> .gitignore
git add .gitignore
git commit -m "Add ${SECRET_FILE} to .gitignore to prevent future commits"

echo "Force pushing cleaned history to remote..."
# Use --force-with-lease for safer force push, but for a new history, --force is often necessary.
# Given git-filter-repo creates a new history, --force is usually required here.
git push --force origin "${TARGET_BRANCH}"
if [ $? -ne 0 ]; then
    echo "Error: Force push failed. You might need to manually inspect the remote repository."
    echo "The local repository in '${TEMP_DIR}/repo_to_clean' is cleaned, but not pushed."
    cd - > /dev/null
    # Do not remove TEMP_DIR so user can inspect
    exit 1
fi
echo "Cleaned history successfully pushed to GitHub."

# Clean up the temporary directory
echo "Cleaning up temporary directory..."
cd - > /dev/null # Go back to the original directory
rm -rf "${TEMP_DIR}"
echo "Temporary directory removed: ${TEMP_DIR}"

echo ""
echo "--------------------------------------------------------"
echo "           Script Finished Successfully!"
echo "--------------------------------------------------------"
echo ""
echo "IMPORTANT NEXT STEPS:"
echo "1.  Delete your *original* local repository folder."
echo "2.  Clone the repository again from GitHub to get the clean history:"
echo "    git clone https://github.com/${GITHUB_USERNAME}/${REPOSITORY_NAME}.git"
echo "3.  Inform any collaborators to also delete their local clones and re-clone."
echo "4.  If you need the content of '${SECRET_FILE}' locally (without tracking), create it manually."
echo "    Remember to never commit it again!"
echo ""
