__all__ = ["io"]
__version__ = "0.0.1"


def run_all_exports() -> None:
    """Run all export scripts sequentially, then archive the data directory.

    This is used both by the CLI entry point (mtb-export-all) and by the
    report-generation shell helper to ensure that all CSVs – including
    demographics – are up to date before analysis.
    """
    from datetime import datetime
    from pathlib import Path
    import shutil

    from .export_participant_meta import export_participant_meta
    from .export_time_spent import export_time_spent
    from .export_speech import export_speech
    from .export_questionnaire_likert import export_questionnaire_likert
    from .export_questionnaire_open import export_questionnaire_open
    from .export_badge_stats import export_badge_stats
    from .export_demographics import export_demographics
    from .io import DEFAULT_INPUT_PATH

    # Core CSV exports
    export_participant_meta()
    export_time_spent()
    export_speech()
    export_questionnaire_likert()
    export_questionnaire_open()
    export_badge_stats()
    export_demographics()

    # After exports, create a timestamped ZIP archive of the data directory
    data_dir: Path = (DEFAULT_INPUT_PATH.parent).resolve()
    archive_root: Path = data_dir.parent / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_name = str((archive_root / f"study-data-{ts}").resolve())
    shutil.make_archive(base_name=base_name, format="zip", root_dir=str(data_dir))


def main_run_all() -> None:
    """Console entry point for mtb-export-all."""
    run_all_exports()

