""" Created on Tue Jul 30 13:31:57 2024
    @author: dcupolillo """

import os
import subprocess


def setup_https_authentication(
        username: str = "dcupolillo",
        email: str = "dario.cupolillo@gmail.com",
        token: str = "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"
) -> None:
    """
    Set up HTTPS authentication for Git with a personal access token.

    Parameters:
    - username (str): Your GitHub username.
    - email (str): Your GitHub email.
    - token (str): Your GitHub personal access token.
    """
    try:
        # Set Git username and email
        subprocess.run(
            ['git', 'config', '--global', 'user.name', username], check=True)
        subprocess.run(
            ['git', 'config', '--global', 'user.email', email], check=True)

        # Store the personal access token in the Git configuration
        subprocess.run(
            ['git', 'config', '--global', 'credential.helper', 'store'],
            check=True)

        # Create a credentials file with the token
        with open(
                os.path.expanduser('~/.git-credentials'), 'w') as cred_file:
            cred_file.write(f"https://{username}:{token}@github.com\n")

        print("HTTPS authentication setup complete")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)


def publish_to_github(
        commit_message: str,
        repo_url: str = "https://github.com/dcupolillo/ROIpy.git",
) -> None:
    """
    Publish the current working directory to a specified GitHub repository.

    Parameters:
    - repo_url (str): The GitHub repository URL.
    - commit_message (str): The commit message to use.
    """
    # Get the current working directory
    project_dir = os.getcwd()

    # Initialize a git repository if it doesn't exist
    if not os.path.exists(os.path.join(project_dir, '.git')):
        subprocess.run(['git', 'init'], check=True)
        subprocess.run(
            ['git', 'remote', 'add', 'origin', repo_url], check=True)

    # Add all files to the staging area
    subprocess.run(['git', 'add', '.'], check=True)

    # Check the status of the repository
    status = subprocess.run(
        ['git', 'status'],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True)
    print("Git status output:\n", status.stdout)

    # Commit the changes
    try:
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        print(commit_result.stdout)
        print(commit_result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during commit: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return

    # Pull the latest changes from the remote repository
    try:
        pull_result = subprocess.run(
            ['git', 'pull', 'origin', 'main', '--rebase'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        print(pull_result.stdout)
        print(pull_result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during pull: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return

    # Push the changes to the remote repository
    try:
        push_result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        print(push_result.stdout)
        print(push_result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during push: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)


def update_to_github(
        commit_message: str,
        repo_url: str = "https://github.com/dcupolillo/ROIpy.git"
) -> None:
    """
    Add all new changes, commit, and push to the remote repository.

    Parameters:
    - repo_url (str): The GitHub repository URL.
    - commit_message (str): The commit message to use.
    """
    try:
        # Add all files to the staging area
        subprocess.run(['git', 'add', '.'], check=True)

        # Commit the changes
        subprocess.run(
            ['git', 'commit', '-m', commit_message], check=True)

        # Pull the latest changes from the remote repository with rebase
        subprocess.run(
            ['git', 'pull', 'origin', 'main', '--rebase'], check=True)

        # Push the changes to the remote repository
        push_result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)

        print(push_result.stdout)
        print(push_result.stderr)

        # Verify repository status
        status = subprocess.run(
            ['git', 'status'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        print("Git status after push:\n", status.stdout)

        print("Update to GitHub complete.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
