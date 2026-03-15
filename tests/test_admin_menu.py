from app.bot.handlers.menu import _format_admin_catalog_health
from app.constants import SupportedLanguage
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
