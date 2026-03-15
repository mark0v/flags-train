import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from app.constants import QUESTION_ORDER, QuizCategory, SupportedLanguage
from app.services.country_store import Country, CountryStore


@dataclass(slots=True)
class Question:
    id: str
    country_code: str
    category: QuizCategory
    prompt: str
    options: list[str]
    correct_option: str
    answer_context: str
    flag_path: Path | None = None


@dataclass(slots=True)
class QuizSession:
    language: SupportedLanguage
    countries_count: int
    categories: list[QuizCategory]
    questions: deque[Question]
    retry_queue: deque[Question] = field(default_factory=deque)
    repeat_later_ids: set[str] = field(default_factory=set)
    answered: int = 0
    mistakes: int = 0

    def current_question(self) -> Question | None:
        if self.questions:
            return self.questions[0]
        if self.retry_queue:
            self.questions = deque(self.retry_queue)
            self.retry_queue = deque()
            return self.questions[0]
        return None

    def on_correct(self) -> None:
        if self.questions:
            question = self.questions.popleft()
            if question.id in self.repeat_later_ids:
                self.retry_queue.append(question)
                self.repeat_later_ids.remove(question.id)
            self.answered += 1

    def on_wrong(self) -> None:
        if self.questions:
            self.mistakes += 1
            self.repeat_later_ids.add(self.questions[0].id)

    def skip_current(self) -> None:
        if self.questions:
            question = self.questions.popleft()
            if question.id in self.repeat_later_ids or question not in self.retry_queue:
                self.retry_queue.append(question)
                self.repeat_later_ids.discard(question.id)
            self.answered += 1

    def progress_text(self) -> str:
        total = self.countries_count * len(self.categories)
        completed = min(self.answered, total)
        return f"{completed}/{total}"


class QuizEngine:
    def __init__(self, store: CountryStore, random_source: random.Random | None = None) -> None:
        self._store = store
        self._random = random_source or random.Random()

    def create_session(
        self,
        language: SupportedLanguage,
        countries_count: int,
        categories: list[QuizCategory],
    ) -> QuizSession:
        if len(self._store.countries) < countries_count:
            raise ValueError("dataset too small")
        selected_countries = self._random.sample(self._store.countries, countries_count)
        questions: list[Question] = []
        for country in selected_countries:
            for category in QUESTION_ORDER:
                if category in categories:
                    questions.append(self._build_question(country, category, language))
        return QuizSession(
            language=language,
            countries_count=countries_count,
            categories=categories,
            questions=deque(questions),
        )

    def _build_question(
        self,
        country: Country,
        category: QuizCategory,
        language: SupportedLanguage,
    ) -> Question:
        correct_option = self._answer_value(country, category, language)
        distractors = self._distractors(country.code, category, language, correct_option)
        options = distractors + [correct_option]
        self._random.shuffle(options)
        prompt, answer_context, flag_path = self._prompt_for(country, category, language)
        return Question(
            id=f"{country.code}:{category.value}",
            country_code=country.code,
            category=category,
            prompt=prompt,
            options=options,
            correct_option=correct_option,
            answer_context=answer_context,
            flag_path=flag_path,
        )

    def _answer_value(
        self,
        country: Country,
        category: QuizCategory,
        language: SupportedLanguage,
    ) -> str:
        if category is QuizCategory.FLAG:
            return country.name(language)
        if category is QuizCategory.CAPITAL:
            return country.capital_name(language)
        if category is QuizCategory.LANGUAGE:
            return country.language_name(language)
        if category is QuizCategory.POPULATION:
            return country.population_label(language)
        return f"{country.currency_label(language)} ({country.currency_code})"

    def _distractors(
        self,
        country_code: str,
        category: QuizCategory,
        language: SupportedLanguage,
        correct_option: str,
    ) -> list[str]:
        values: list[str] = []
        for country in self._store.countries:
            if country.code == country_code:
                continue
            candidate = self._answer_value(country, category, language)
            if candidate != correct_option and candidate not in values:
                values.append(candidate)
        return self._random.sample(values, 3)

    def _prompt_for(
        self,
        country: Country,
        category: QuizCategory,
        language: SupportedLanguage,
    ) -> tuple[str, str, Path | None]:
        country_name = country.name(language)
        if category is QuizCategory.FLAG:
            prompts = {
                "ru": "Какая это страна?",
                "en": "Which country is this?",
                "de": "Welches Land ist das?",
            }
            return prompts[language.value], country_name, self._store.flag_path(country)
        if category is QuizCategory.CAPITAL:
            prompts = {
                "ru": f"Столица страны <b>{country_name}</b>?",
                "en": f"What is the capital of <b>{country_name}</b>?",
                "de": f"Was ist die Hauptstadt von <b>{country_name}</b>?",
            }
            return prompts[language.value], country.capital_name(language), None
        if category is QuizCategory.LANGUAGE:
            prompts = {
                "ru": f"Основной официальный язык страны <b>{country_name}</b>?",
                "en": f"What is the main official language of <b>{country_name}</b>?",
                "de": f"Was ist die wichtigste Amtssprache von <b>{country_name}</b>?",
            }
            return prompts[language.value], country.language_name(language), None
        if category is QuizCategory.POPULATION:
            prompts = {
                "ru": f"Население страны <b>{country_name}</b>?",
                "en": f"What is the population of <b>{country_name}</b>?",
                "de": f"Wie gross ist die Bevolkerung von <b>{country_name}</b>?",
            }
            return prompts[language.value], country.population_label(language), None

        prompts = {
            "ru": f"Валюта страны <b>{country_name}</b>?",
            "en": f"What is the currency of <b>{country_name}</b>?",
            "de": f"Was ist die Wahrung von <b>{country_name}</b>?",
        }
        answer = f"{country.currency_label(language)} ({country.currency_code})"
        return prompts[language.value], answer, None
