from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_documents_exist():
    for path in (
        'README.md', 'requirements.txt', 'docs/interfaces/README.md',
        'docs/GIT_WORKFLOW.md', 'docs/REPORTING.md',
    ):
        assert (ROOT / path).is_file(), path


def test_member_directories_exist():
    for name in (
        'computer-vision', 'ai-dataset', 'machine_learning',
        'control-algorithm', 'real-time-application', 'integration-testing',
    ):
        assert (ROOT / name / 'README.md').is_file(), name
