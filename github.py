""" Created on Tue Jul 30 13:31:57 2024
    @author: dcupolillo """

import os
import subprocess


github_username = "dcupolillo"
github_email = "dario.cupolillo@gmail.com"
personal_access_token = "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"


def setup_https_authentication(username, email, token):
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


def publish_to_github(repo_url, commit_message):
    """
    Add all files to the repository for the first time, commit, and push to the remote repository.

    Parameters:
    - repo_url (str): The GitHub repository URL.
    - commit_message (str): The commit message to use.
    """
    try:
        # Get the current working directory
        project_dir = os.getcwd()
        
        # Initialize a git repository if it doesn't exist
        if not os.path.exists(os.path.join(project_dir, '.git')):
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
        
        # Add all files to the staging area
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit the changes
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push the changes to the remote repository
        push_result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(push_result.stdout)
        print(push_result.stderr)
        
        print("Initial addition to GitHub complete.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)


def update_to_github(repo_url, commit_message):
    """
    Add all new changes, commit, and push to the remote repository.

    Parameters:
    - repo_url (str): The GitHub repository URL.
    - commit_message (str): The commit message to use.
    """
    try:
        # Get the current working directory
        project_dir = os.getcwd()
        
        # Add all files to the staging area
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit the changes
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Pull the latest changes from the remote repository with rebase
        try:
            pull_result = subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(pull_result.stdout)
            print(pull_result.stderr)
        except subprocess.CalledProcessError as e:
            if "It seems that there is already a rebase-merge directory" in e.stderr:
                print(f"Rebase conflict detected: {e}")
                print("Aborting the ongoing rebase and trying again.")
                resolve_rebase_conflicts()
                return
            print(f"Error occurred during pull: {e}")
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)
            return
        
        # Push the changes to the remote repository
        push_result = subprocess.run(['git', 'push', 'origin', 'main'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(push_result.stdout)
        print(push_result.stderr)
        
        print("Update to GitHub complete.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)