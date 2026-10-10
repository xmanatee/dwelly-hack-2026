"""Dataset selection for execution and saved-answer grading."""

from dwelly_bot.adapters.banking import BankingAdapter
from dwelly_bot.contracts import DatasetAdapter

ADAPTERS = {"dwelly-banking": BankingAdapter}


def adapter_for(name: str) -> DatasetAdapter:
    return ADAPTERS[name]()
