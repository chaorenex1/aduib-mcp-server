from abc import ABC, abstractmethod


class HtmlParser(ABC):
    """Abstract base class for HTML parsers."""
    @abstractmethod
    def parse(self, html_content):
        ...