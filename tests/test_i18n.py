from app.constants import QuizCategory, SupportedLanguage
from app.services.i18n import I18nService


def test_i18n_resolves_text_and_categories() -> None:
    service = I18nService()

    assert service.text("main_menu", SupportedLanguage.EN) == "Main menu"
    assert service.category_label(QuizCategory.CURRENCY, SupportedLanguage.DE) == "Wahrung"
