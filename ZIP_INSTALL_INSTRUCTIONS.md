# Apply this ZIP to the existing Git repository

This archive is a **non-destructive overlay**: it does not include or delete the repository's legacy folders. It **replaces** `README.md` and `.gitignore`, and adds the listed files.

## Windows PowerShell (recommended)
1. Download the ZIP and extract it.
2. Open PowerShell in your local clone of `hand-gesture-driving-simulator`.
3. Check for uncommitted changes: `git status`. Save/commit your work before continuing.
4. Update main: `git switch main` then `git pull origin main`.
5. Copy the **contents** of the extracted `hand-gesture-driving-simulator-setup` folder into your repository root (merge folders; approve overwriting README.md and .gitignore).
6. Review changes: `git status` and `git diff`.
7. Test (after installing pytest): `python -m pytest`.
8. Commit and push:
   ```powershell
   git add README.md .gitignore requirements.txt pytest.ini .github docs computer-vision ai-dataset machine-learning control-algorithm real-time-application integration-testing tests ZIP_INSTALL_INSTRUCTIONS.md
   git commit -m "chore: initialize six-member Python project structure"
   git push origin main
   ```

If `main` is protected, create a branch and PR instead of pushing directly. Do not force-push.

The ZIP itself is not a Git commit; Git history remains in the existing clone. Do not replace the `.git` folder.
