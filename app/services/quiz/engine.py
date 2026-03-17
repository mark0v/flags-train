import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from app.constants import QUESTION_ORDER, QuizCategory, SupportedLanguage
from app.services.country_store import Country, CountryStore
from app.services.quiz_display import quiz_option_label


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
    is_retry: bool = False
    option_labels: list[str] | None = None


@dataclass(slots=True)
class QuestionResolution:
    question: Question
    resolved: bool
    outcome: str | None = None
    selected_option: str | None = None


@dataclass(slots=True)
class QuizSession:
    language: SupportedLanguage
    countries_count: int
    categories: list[QuizCategory]
    questions: deque[Question]
    total_questions: int
    wrong_attempts_by_question: dict[str, int] = field(default_factory=dict)
    resolved_questions: int = 0
    correct_answers: int = 0
    skipped_answers: int = 0
    mistakes: int = 0

    def current_question(self) -> Question | None:
        return self.questions[0] if self.questions else None

    def on_correct(self, selected_option: str) -> QuestionResolution:
        question = self.questions.popleft()
        self.resolved_questions += 1
        self.correct_answers += 1
        return QuestionResolution(
            question,
            resolved=True,
            outcome="correct",
            selected_option=selected_option,
        )

    def on_wrong(self) -> None:
        question = self.questions[0]
        self.mistakes += 1
        self.wrong_attempts_by_question[question.id] = (
            self.wrong_attempts_by_question.get(question.id, 0) + 1
        )

    def resolve_incorrect(self) -> QuestionResolution:
        question = self.questions.popleft()
        self.resolved_questions += 1
        return QuestionResolution(question, resolved=True, outcome="incorrect")

    def skip_current(self) -> QuestionResolution:
        question = self.questions.popleft()
        self.resolved_questions += 1
        self.skipped_answers += 1
        return QuestionResolution(question, resolved=True, outcome="skipped")

    def progress_text(self) -> str:
        if self.total_questions == 0:
            return "0/0"
        current = (
            self.resolved_questions + 1
            if self.current_question() is not None
            else self.total_questions
        )
        return f"{min(current, self.total_questions)}/{self.total_questions}"

    def wrong_attempts(self, question_id: str) -> int:
        return self.wrong_attempts_by_question.get(question_id, 0)

    def remove_country(self, country_code: str) -> int:
        remaining_questions = [
            question for question in self.questions if question.country_code != country_code
        ]
        removed_count = len(self.questions) - len(remaining_questions)
        if removed_count:
            self.questions = deque(remaining_questions)
            self.total_questions -= removed_count
        return removed_count


class QuizEngine:
    def __init__(self, store: CountryStore, random_source: random.Random | None = None) -> None:
        self._store = store
        self._random = random_source or random.Random()

    def create_session(
        self,
        language: SupportedLanguage,
        countries_count: int,
        categories: list[QuizCategory],
        priority_country_codes: list[str] | None = None,
        excluded_country_codes: list[str] | None = None,
    ) -> QuizSession:
        available_countries = self._available_countries(excluded_country_codes or [])
        if len(available_countries) < countries_count:
            raise ValueError("dataset too small")
        selected_countries = self._select_countries(
            available_countries,
            countries_count,
            priority_country_codes or [],
        )
        questions: list[Question] = []
        for country in selected_countries:
            for category in QUESTION_ORDER:
                if category in categories:
                    questions.append(self._build_question(country, category, language))
        return QuizSession(
            language=language,
            countries_count=countries_count,
            categories=categories,
            total_questions=len(questions),
            questions=deque(questions),
        )

    def _available_countries(self, excluded_country_codes: list[str]) -> list[Country]:
        excluded = set(excluded_country_codes)
        return [country for country in self._store.countries if country.code not in excluded]

    def _select_countries(
        self,
        available_countries: list[Country],
        countries_count: int,
        priority_country_codes: list[str],
    ) -> list[Country]:
        countries_by_code = {country.code: country for country in available_countries}
        selected: list[Country] = []
        seen_codes: set[str] = set()

        for code in priority_country_codes:
            country = countries_by_code.get(code)
            if country is None or code in seen_codes:
                continue
            selected.append(country)
            seen_codes.add(code)
            if len(selected) == countries_count:
                return selected

        remaining = [country for country in available_countries if country.code not in seen_codes]
        selected.extend(self._random.sample(remaining, countries_count - len(selected)))
        return selected

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
        option_labels = [quiz_option_label(option, category, language) for option in options]
        prompt, answer_context, flag_path = self._prompt_for(country, category, language)
        return Question(
            id=f"{country.code}:{category.value}",
            country_code=country.code,
            category=category,
            prompt=prompt,
            options=options,
            option_labels=option_labels,
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
        flag_path = self._store.flag_path(country)
        if category is QuizCategory.FLAG:
            prompts = {
                "ru": "Какая это страна?",
                "en": "Which country is this?",
                "de": "Welches Land ist das?",
            }
            return prompts[language.value], country_name, flag_path
        if category is QuizCategory.CAPITAL:
            prompts = {
                "ru": f"Столица страны <b>{country_name}</b>?",
                "en": f"What is the capital of <b>{country_name}</b>?",
                "de": f"Was ist die Hauptstadt von <b>{country_name}</b>?",
            }
            return prompts[language.value], country.capital_name(language), flag_path
        if category is QuizCategory.LANGUAGE:
            prompts = {
                "ru": f"Основной официальный язык страны <b>{country_name}</b>?",
                "en": f"What is the main official language of <b>{country_name}</b>?",
                "de": f"Was ist die wichtigste Amtssprache von <b>{country_name}</b>?",
            }
            return prompts[language.value], country.language_name(language), flag_path
        if category is QuizCategory.POPULATION:
            prompts = {
                "ru": f"Население страны <b>{country_name}</b>?",
                "en": f"What is the population of <b>{country_name}</b>?",
                "de": f"Wie gross ist die Bevolkerung von <b>{country_name}</b>?",
            }
            return prompts[language.value], country.population_label(language), flag_path

        prompts = {
            "ru": f"Валюта страны <b>{country_name}</b>?",
            "en": f"What is the currency of <b>{country_name}</b>?",
            "de": f"Was ist die Wahrung von <b>{country_name}</b>?",
        }
        answer = f"{country.currency_label(language)} ({country.currency_code})"
        return prompts[language.value], answer, flag_path
