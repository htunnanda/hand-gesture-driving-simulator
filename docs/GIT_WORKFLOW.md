# Git collaboration rules

## Branch convention
- `main`: reviewed, stable code only
- `feature/computer-vision`: Member 1
- `feature/ai-dataset`: Member 2
- `feature/machine-learning`: Member 3
- `feature/control-algorithm`: Member 4
- `feature/real-time-application`: Member 5
- `feature/integration-testing`: Member 6

Branches should be created by team members when work begins. This ZIP does not create remote branches.

## Pull request workflow
1. Start from updated `main` and work on your feature branch.
2. Commit scoped changes. Do not commit personal webcam captures, secrets, or `.venv`.
3. Run `python -m pytest` and any relevant manual camera/game checks.
4. Update interface docs and the member process report when relevant.
5. Open a pull request targeting `main`; describe changes, tests, known issues.
6. Member 6 reviews every PR and coordinates fixes with the code owner.
7. Merge only after review and successful relevant tests.

## Member 6 ongoing responsibilities
- Review **all members' code continuously**, not only at the final integration stage.
- Track code quality, bugs, module interfaces, performance, and privacy risks.
- Manage branches, pull requests, merge conflicts, and integration schedule.
- Collect process reports from all six members after every working session.
- Publish consolidated progress, blockers, and next actions.
- Verify integrated application behavior and coordinate final release.

Repository owner/admin should configure branch protection for `main`, PR review requirements, and CI once ready. This ZIP cannot change GitHub settings.
