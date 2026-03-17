from app.bot.handlers.menu import _format_stats
from app.constants import QuizCategory, SupportedLanguage
from app.services.i18n import I18nService
from app.services.statistics import CategoryProgressStat, UserStatsSummary


def test_format_stats_includes_category_breakdown() -> None:
    rendered = _format_stats(
        UserStatsSummary(
            quizzes_started=4,
            quizzes_completed=3,
            quizzes_abandoned=1,
            resolved_questions=12,
            correct_answers=9,
            skipped_answers=3,
            wrong_attempts=2,
            tracked_items=4,
            mastered_items=1,
            due_items=2,
            completed_last_7_days=2,
            category_breakdown=[
                CategoryProgressStat(
                    category=QuizCategory.FLAG,
                    tracked_items=2,
                    mastered_items=1,
                    due_items=0,
                    correct_answers=3,
                    attempts_count=4,
                ),
                CategoryProgressStat(
                    category=QuizCategory.CAPITAL,
                    tracked_items=2,
                    mastered_items=0,
                    due_items=2,
                    correct_answers=1,
                    attempts_count=3,
                ),
            ],
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Progress by category" in rendered
    assert "Abandoned: <b>1</b>" in rendered
    assert "Completion rate: <b>75%</b>" in rendered
    assert "Completed in 7 days: <b>2</b>" in rendered
    assert "Skipped:" not in rendered
    assert "Best focus right now: <b>Capital</b>" in rendered
    assert "Flag: due <b>0</b>, mastered <b>1/2</b>, accuracy <b>75%</b>" in rendered
    assert "Capital: due <b>2</b>, mastered <b>0/2</b>, accuracy <b>33%</b>" in rendered
    assert "Countries ready for review mode: <b>0</b>" in rendered
    assert "Review-ready: <b>not yet</b>" in rendered


def test_format_stats_hides_hidden_categories_from_breakdown() -> None:
    rendered = _format_stats(
        UserStatsSummary(
            quizzes_started=2,
            quizzes_completed=1,
            resolved_questions=4,
            correct_answers=2,
            wrong_attempts=2,
            tracked_items=1,
            mastered_items=1,
            due_items=0,
            completed_last_7_days=1,
            category_breakdown=[
                CategoryProgressStat(
                    category=QuizCategory.LANGUAGE,
                    tracked_items=1,
                    mastered_items=1,
                    due_items=0,
                    correct_answers=3,
                    attempts_count=3,
                ),
            ],
        ),
        SupportedLanguage.EN,
        I18nService(),
    )

    assert "Progress by category" not in rendered
    assert "Best focus right now" not in rendered
    assert "Language" not in rendered
