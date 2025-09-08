import base64
import logging
import urllib

from component.crawl4ai.crawler_pool import html_parser
from component.crawl4ai.html_parser.html_parser import HtmlParser

logger=logging.getLogger(__name__)

def decode_bing_url(bing_url: str) -> str:
    try:
        url = urllib.parse.urlparse(bing_url)
        query = urllib.parse.parse_qs(url.query)
        encoded_url_list = query.get('u')
        if not encoded_url_list or not encoded_url_list[0]:
            return bing_url  # Return original if no 'u' parameter

        encoded_url = encoded_url_list[0]
        # Remove the 'a1' prefix and decode Base64
        base64_part = encoded_url[2:]
        try:
            decoded_bytes = base64.b64decode(base64_part)
            decoded_url = decoded_bytes.decode('utf-8')
        except Exception as e:
            logger.warning(f"Failed to base64 decode Bing URL: {e}")
            return bing_url

        # Validate the decoded URL
        if decoded_url.startswith('http'):
            return decoded_url

        return bing_url  # Return original if decoded URL is invalid
    except Exception as error:
        logger.warning(f"Failed to decode Bing URL: {error}")
        return bing_url  # Return original URL if decoding fails

@html_parser("bing")
class BingHtmlParser(HtmlParser):
    """A parser for Bing search result HTML content."""
    def parse(self, html_content):
        """Parse the HTML content and extract search results."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, '"lxml-xml')
        results = []

        for item in soup.select('#b_results h2'):
            node = item.select_one('a')
            if node and node.get('href'):
                title = node.get_text(strip=True)
                link = decode_bing_url(node['href'])
                snippet = item.find_next_sibling('p')
                results.append({'title': title, 'link': link, 'snippet': snippet.get_text(strip=True)})

        logger.debug(f"results: {results}")
        return results