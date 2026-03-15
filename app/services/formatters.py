def format_population_short(population: int, language: str) -> str:
    millions = round(population / 1_000_000)
    if language == "ru":
        return f"{millions} млн"
    if language == "de":
        return f"{millions} Mio."
    return f"{millions}M"
