import random
from collections import deque
from dataclasses import dataclass, field, replace
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
    is_retry: bool = False


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
    retry_queue: deque[Question] = field(default_factory=deque)
    repeat_later_ids: set[str] = field(default_factory=set)
    wrong_attempts_by_question: dict[str, int] = field(default_factory=dict)
    resolved_questions: int = 0
    correct_answers: int = 0
    skipped_answers: int = 0
    mistakes: int = 0

    def current_question(self) -> Question | None:
        if self.questions:
            return self.questions[0]
        if self.retry_queue:
            self.questions = deque(self.retry_queue)
            self.retry_queue = deque()
            return self.questions[0]
        return None

    def on_correct(self, selected_option: str) -> QuestionResolution:
        question = self.questions.popleft()
        if question.is_retry:
            self.repeat_later_ids.discard(question.id)
            self.resolved_questions += 1
            self.correct_answers += 1
            return QuestionResolution(
                question,
                resolved=True,
                outcome="correct",
                selected_option=selected_option,
            )
        if question.id in self.repeat_later_ids:
            return QuestionResolution(
                question,
                resolved=False,
                selected_option=selected_option,
            )
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
        if question.id not in self.repeat_later_ids:
            self.repeat_later_ids.add(question.id)
            self.retry_queue.append(replace(question, is_retry=True))

    def skip_current(self) -> QuestionResolution:
        question = self.questions.popleft()
        if question.is_retry:
            self.repeat_later_ids.discard(question.id)
            self.resolved_questions += 1
            self.skipped_answers += 1
            return QuestionResolution(question, resolved=True, outcome="skipped")
        if question.id in self.repeat_later_ids:
            return QuestionResolution(question, resolved=False)
        self.resolved_questions += 1
        self.skipped_answers += 1
        return QuestionResolution(question, resolved=True, outcome="skipped")

    def progress_text(self) -> str:
        completed = min(self.resolved_questions, self.total_questions)
        return f"{completed}/{self.total_questions}"

    def wrong_attempts(self, question_id: str) -> int:
        return self.wrong_attempts_by_question.get(question_id, 0)


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
    ) -> QuizSession:
        if len(self._store.countries) < countries_count:
            raise ValueError("dataset too small")
        selected_countries = self._select_countries(countries_count, priority_country_codes or [])
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

    def _select_countries(
        self,
        countries_count: int,
        priority_country_codes: list[str],
    ) -> list[Country]:
        countries_by_code = {country.code: country for country in self._store.countries}
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

        remaining = [country for country in self._store.countries if country.code not in seen_codes]
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
