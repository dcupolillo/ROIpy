""" Created on Tue Jul 30 13:31:57 2024
    @author: dcupolillo """

import os
import subprocess


class GitRepository:

    def __init__(
            self,
            repo_url: str = "https://github.com/dcupolillo/ROIpy.git",
            username: str = "dcupolillo",
            email: str = "dario.cupolillo@gmail.com",
    ) -> None:

        self.url = repo_url
        self.repo_path = os.getcwd()

        if username and email:
            self.setup_https_authentication(username, email)

    def run_git_command(self, command):
        """
        Run a Git command in the repository.
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(result.stdout)
            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)
            return e.stderr

    def setup_https_authentication(self, username, email):
        """
        Set up HTTPS authentication for Git without a personal access token.

        Parameters:
        - username (str): Your GitHub username.
        - email (str): Your GitHub email.
        """
        try:
            # Set Git username and email
            subprocess.run(
                ['git', 'config', '--global', 'user.name', username],
                check=True)
            subprocess.run(
                ['git', 'config', '--global', 'user.email', email],
                check=True)

            # Enable credential caching for 15 mins
            subprocess.run(
                ['git', 'config', '--global', 'credential.helper', 'cache'],
                check=True)

            print("HTTPS authentication setup complete")

        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)

    def init(self):
        return self.run_git_command(['git', 'init'])

    def clone(self, repo_url):
        return self.run_git_command(['git', 'clone', repo_url, self.url])

    def status(self):
        return self.run_git_command(['git', 'status'])

    def add(self, file_name):
        return self.run_git_command(['git', 'add', file_name])

    def add_all(self):
        return self.run_git_command(['git', 'add', '-A'])

    def commit(self, message):
        return self.run_git_command(['git', 'commit', '-m', message])

    def remove(self, file_name):
        return self.run_git_command(['git', 'rm', '-r', file_name])

    def branch(self):
        return self.run_git_command(['git', 'branch'])

    def branch_all(self):
        return self.run_git_command(['git', 'branch', '-a'])

    def create_branch(self, branch_name):
        return self.run_git_command(['git', 'branch', branch_name])

    def delete_branch(self, branch_name):
        return self.run_git_command(['git', 'branch', '-d', branch_name])

    def delete_remote_branch(self, branch_name):
        return self.run_git_command(
            ['git', 'push', 'origin', '--delete', branch_name])

    def checkout(self, branch_name):
        return self.run_git_command(['git', 'checkout', branch_name])

    def checkout_new_branch(self, branch_name):
        return self.run_git_command(['git', 'checkout', '-b', branch_name])

    def checkout_remote_branch(self, branch_name):
        return self.run_git_command(
            ['git', 'checkout', '-b', branch_name, f'origin/{branch_name}'])

    def rename_branch(self, old_name, new_name):
        return self.run_git_command(
            ['git', 'branch', '-m', old_name, new_name])

    def merge(self, branch_name):
        return self.run_git_command(['git', 'merge', branch_name])

    def stash(self):
        return self.run_git_command(['git', 'stash'])

    def stash_clear(self):
        return self.run_git_command(['git', 'stash', 'clear'])

    def push(self, branch_name):
        return self.run_git_command(['git', 'push', 'origin', branch_name])

    def push_set_upstream(self, branch_name):
        return self.run_git_command(
            ['git', 'push', '-u', 'origin', branch_name])

    def pull(self):
        return self.run_git_command(['git', 'pull'])

    def pull_branch(self, branch_name):
        return self.run_git_command(['git', 'pull', 'origin', branch_name])

    def add_remote(self, repo_url):
        return self.run_git_command(
            ['git', 'remote', 'add', 'origin', repo_url])

    def set_remote_url(self, repo_url):
        return self.run_git_command(
            ['git', 'remote', 'set-url', 'origin', repo_url])

    def log(self):
        return self.run_git_command(['git', 'log'])

    def log_summary(self):
        return self.run_git_command(['git', 'log', '--summary'])

    def log_oneline(self):
        return self.run_git_command(['git', 'log', '--oneline'])

    def diff(self, source_branch, target_branch):
        return self.run_git_command(
            ['git', 'diff', source_branch, target_branch])
