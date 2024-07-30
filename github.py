""" Created on Tue Jul 30 13:31:57 2024
    @author: dcupolillo """

import os
import subprocess


def publish_to_github(
        repo_url,
        commit_message
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

    # Commit the changes
    subprocess.run(['git', 'commit', '-m', commit_message], check=True)

    # Push the changes to the remote repository
    subprocess.run(['git', 'push', 'origin', 'master'], check=True)