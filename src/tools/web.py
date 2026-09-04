import httpx
from typing import Any, Dict
from bs4 import BeautifulSoup
from .base import BaseTool
from .schemas import WebSearchInput, WebExtractInput
from ..config import settings

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web using the configured search API."
    input_schema = WebSearchInput

    def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        if not settings.search_api_key:
            return {"success": False, "error": "Search API is not configured. Missing SEARCH_API_KEY."}
            
        try:
            headers = {"User-Agent": "AgentOS/1.0"}
            response = httpx.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for a in soup.find_all('a', class_='result__url'):
                url = a.get('href', '')
                title_elem = a.find_previous('h2', class_='result__title')
                title = title_elem.text.strip() if title_elem else ""
                snippet_elem = a.find_next('a', class_='result__snippet')
                snippet = snippet_elem.text.strip() if snippet_elem else ""
                
                if "duckduckgo.com/l/?uddg=" in url:
                    from urllib.parse import unquote
                    url = unquote(url.split("uddg=")[1].split("&")[0])
                
                results.append({"title": title, "url": url, "snippet": snippet})
                if len(results) >= 5:
                    break
                    
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

class WebExtractTool(BaseTool):
    name = "web_extract"
    description = "Extract readable text from a URL."
    input_schema = WebExtractInput

    def execute(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            headers = {"User-Agent": "AgentOS/1.0"}
            response = httpx.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text(separator='\n')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            title = soup.title.string if soup.title else ""
            
            return {"success": True, "url": url, "title": title, "text": text}
        except httpx.TimeoutException:
             return {"success": False, "error": "Request timed out"}
        except httpx.HTTPError as e:
             return {"success": False, "error": f"HTTP error occurred: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
