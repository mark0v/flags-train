from app.bot.handlers.menu import _format_stats
from app.constants import QuizCategory, SupportedLanguage
from app.services.i18n import I18nService
from app.services.statistics import CategoryProgressStat, UserStatsSummary


def test_format_stats_includes_category_breakdown() -> None:
    rendered = _format_stats(
        UserStatsSummary(
            quizzes_started=4,
            quizzes_completed=3,
            resolved_questions=12,
            correct_answers=9,
            skipped_answers=3,
            wrong_attempts=2,
            tracked_items=4,
            mastered_items=1,
            due_items=2,
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
    assert "Best focus right now: <b>Capital</b>" in rendered
    assert "• Flag: due <b>0</b>, mastered <b>1/2</b>, accuracy <b>75%</b>" in rendered
    assert "• Capital: due <b>2</b>, mastered <b>0/2</b>, accuracy <b>33%</b>" in rendered
