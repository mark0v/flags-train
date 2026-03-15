from app.bot.handlers.menu import (
    _format_admin_catalog_dashboard,
    _format_admin_catalog_health,
    _format_admin_dataset_validation,
    _format_admin_sync_confirmation,
    _format_admin_sync_error,
    _format_admin_sync_no_changes,
    _format_admin_sync_preview,
    _format_admin_sync_result,
)
from app.constants import SupportedLanguage
from app.services.admin_catalog import AdminCatalogDashboard
from app.services.catalog_health import CatalogHealthReport
from app.services.catalog_sync_preview import CatalogSyncPreview
from app.services.dataset_validation import DatasetValidationReport
from app.services.i18n import I18nService


def test_format_admin_catalog_health_uses_ok_status_for_healthy_report() -> None:
    text = _format_admin_catalog_health(
        dataset_count=193,
        db_count=193,
        missing_in_db=[],
        stale_in_db=[],
        missing_flag_files=[],
        language=SupportedLanguage.EN,
        i18n=I18nService(),
    )

    assert "Status: <b>OK</b>" in text
    assert "Missing in DB: <b>-</b>" in text


def test_format_admin_catalog_health_marks_issue_and_truncates_lists() -> None:
    text = _format_admin_catalog_health(
        dataset_count=193,
        db_count=190,
        missing_in_db=["ARG", "BRA", "CHL", "DEU", "ESP", "FRA"],
        stale_in_db=["OLD"],
        missing_flag_files=["ARG"],
        language=SupportedLanguage.EN,
        i18n=I18nService(),
    )

    assert "Status: <b>Issues found</b>" in text
    assert "Missing in DB: <b>ARG, BRA, CHL, DEU, ESP (+1)</b>" in text
    assert "Stale in DB: <b>OLD</b>" in text


def test_format_admin_catalog_dashboard_for_valid_state() -> None:
    text = _format_admin_catalog_dashboard(
        AdminCatalogDashboard(
            validation=DatasetValidationReport(
                is_valid=True,
                countries_count=193,
                first_country_code="AFG",
                last_country_code="ZWE",
            ),
            health=CatalogHealthReport(
                dataset_count=193,
                db_count=190,
                missing_in_db=["ARG"],
                stale_in_db=["OLD"],
                missing_flag_files=[],
            ),
            preview=CatalogSyncPreview(
                dataset_count=193,
                db_count=190,
                to_create=["ARG"],
                to_update=[],
                to_delete=["OLD"],
            ),
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Dataset: <b>Dataset is valid</b>" in text
    assert "Health check: <b>Issues found</b>" in text
    assert "Pending sync: <b>yes</b>" in text


def test_format_admin_catalog_dashboard_for_invalid_state() -> None:
    text = _format_admin_catalog_dashboard(
        AdminCatalogDashboard(
            validation=DatasetValidationReport(
                is_valid=False,
                error="Dataset is empty.",
            ),
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Dataset: <b>Dataset is invalid</b>" in text
    assert "Error: <b>Dataset is empty.</b>" in text


def test_format_admin_dataset_validation_for_valid_report() -> None:
    text = _format_admin_dataset_validation(
        DatasetValidationReport(
            is_valid=True,
            countries_count=193,
            first_country_code="AFG",
            last_country_code="ZWE",
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Status: <b>Dataset is valid</b>" in text
    assert "Countries: <b>193</b>" in text


def test_format_admin_dataset_validation_for_invalid_report() -> None:
    text = _format_admin_dataset_validation(
        DatasetValidationReport(
            is_valid=False,
            error="Missing flag file for DEU: de.svg",
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Status: <b>Dataset is invalid</b>" in text
    assert "Error: <b>Missing flag file for DEU: de.svg</b>" in text


def test_format_admin_sync_preview_uses_counts_and_truncated_lists() -> None:
    text = _format_admin_sync_preview(
        CatalogSyncPreview(
            dataset_count=193,
            db_count=190,
            to_create=["ARG", "BRA", "CHL", "DEU", "ESP", "FRA"],
            to_update=["UKR"],
            to_delete=["OLD"],
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Will create: <b>6</b> (ARG, BRA, CHL, DEU, ESP (+1))" in text
    assert "Will update: <b>1</b> (UKR)" in text
    assert "Will delete: <b>1</b> (OLD)" in text


def test_format_admin_sync_confirmation_shows_planned_changes() -> None:
    text = _format_admin_sync_confirmation(
        CatalogSyncPreview(
            dataset_count=193,
            db_count=190,
            to_create=["ARG"],
            to_update=["UKR"],
            to_delete=["OLD"],
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "The following changes will be applied to the `countries` table." in text
    assert "Create: <b>1</b> (ARG)" in text
    assert "Continue?" in text


def test_format_admin_sync_result_reports_completed_counts() -> None:
    text = _format_admin_sync_result(
        CatalogSyncPreview(
            dataset_count=193,
            db_count=190,
            to_create=["ARG"],
            to_update=["UKR"],
            to_delete=["OLD"],
        ),
        synced_count=193,
        language=SupportedLanguage.EN,
        i18n=I18nService(),
    )

    assert "Final catalog size: <b>193</b>" in text
    assert "Created: <b>1</b>" in text
    assert "Updated: <b>1</b>" in text
    assert "Deleted: <b>1</b>" in text


def test_format_admin_sync_no_changes_reports_up_to_date_state() -> None:
    text = _format_admin_sync_no_changes(
        CatalogSyncPreview(
            dataset_count=193,
            db_count=193,
            to_create=[],
            to_update=[],
            to_delete=[],
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "The catalog is already in sync." in text
    assert "Dataset countries: <b>193</b>" in text


def test_format_admin_sync_error_shows_specific_reason() -> None:
    text = _format_admin_sync_error(
        "Dataset is empty.",
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Error: <b>Dataset is empty.</b>" in text
