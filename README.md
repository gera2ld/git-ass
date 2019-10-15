# git-ass

A custom command for git to support branch alias and association.

- The main script is written in pure Python 3 and has no third party dependencies.
- The autocomplete script works for Zsh.

## Installation

1. Clone the project

   ```sh
   $ git clone https://github.com/gera2ld/git-ass.git
   ```

1. Add executable path

   ```sh
   export PATH=$PATH:/path/to/git-ass/bin
   ```

1. Enable autocompletion for Zsh

   ```sh
   # ~/.zshrc

   source path/to/git-ass/scripts/init.zsh
   ```

## Usage

Abbreviation is recommended:

```sh
alias a='git ass'
```

- Set base

  E.g. add current branch as a development branch, and expect it to be merged into the release branch `release-1.0`.

  ```sh
  $ git ass add -B release-1.0
  ```

- Alias and description

  E.g. add alias `awesome` and a description to current branch.

  ```sh
  $ git ass add -a awesome -d 'This is an awesome branch'
  ```

- Show information of current branch

  ```sh
  # Show all ancestors
  $ git ass info

  # Show specified property of current branch
  $ git ass info -p alias
  ```

- List recorded branches

  ```sh
  $ git ass list
  ```

- Check out branch by alias

  ```sh
  # Check out `awesome`
  $ git ass checkout awesome
  # or
  $ a co awesome
  ```

- Rebase

  E.g. the current branch is a development branch and based on the release branch `release-1.0` as described above,
  then the following command will rebase the current branch on top of the release branch.

  ```sh
  $ git ass rebase
  ```

- Find a branch by alias

  ```sh
  $ git ass find awesome
  # or
  $ a f awesome
  ```

- Use with git

  ```sh
  $ git checkout `git ass find awesome`
  # or
  $ gco `a f awesome`
  ```

- Purge locally merged branches

  ```sh
  $ git ass purge
  ```

- Prune inexistent branches

  ```sh
  $ git ass prune
  ```
