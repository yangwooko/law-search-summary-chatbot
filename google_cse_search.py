import os
import requests
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import time
from bs4 import BeautifulSoup
import re
from law_article_extractor import extract_law_articles


class GoogleCSESearch:
    """구글 Custom Search Engine을 사용한 웹 검색 클래스"""

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_CSE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")

        if not self.api_key or not self.cse_id:
            raise ValueError(
                "GOOGLE_CSE_API_KEY와 GOOGLE_CSE_ID가 .env 파일에 설정되어야 합니다."
            )

        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        구글 CSE로 검색을 수행합니다.

        Args:
            query: 검색할 쿼리
            num_results: 반환할 결과 수 (최대 10개)

        Returns:
            검색 결과 리스트
        """
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10),  # 구글 CSE는 한 번에 최대 10개 결과
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            if "items" not in data:
                return []

            results = []
            for item in data["items"]:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", ""),
                }
                results.append(result)

            return results

        except requests.exceptions.RequestException as e:
            print(f"검색 중 오류 발생: {e}")
            return []

    def search_with_pagination(self, query: str, total_results: int = 20) -> List[Dict]:
        """
        페이지네이션을 사용하여 더 많은 검색 결과를 가져옵니다.

        Args:
            query: 검색할 쿼리
            total_results: 총 가져올 결과 수

        Returns:
            검색 결과 리스트
        """
        all_results = []
        start_index = 1

        while len(all_results) < total_results:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(10, total_results - len(all_results)),
                "start": start_index,
            }

            try:
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if "items" not in data:
                    break

                for item in data["items"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "displayLink": item.get("displayLink", ""),
                    }
                    all_results.append(result)

                # 다음 페이지로 이동
                start_index += 10

                # API 호출 제한을 위한 지연
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"페이지네이션 검색 중 오류 발생: {e}")
                break

        return all_results[:total_results]

    def extract_text_from_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        URL에서 텍스트를 추출합니다.

        Args:
            url: 텍스트를 추출할 URL
            timeout: 요청 타임아웃 (초)

        Returns:
            추출된 텍스트 또는 None
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # BeautifulSoup을 사용한 HTML 파싱
            soup = BeautifulSoup(response.content, "html.parser")

            # 불필요한 태그들 제거
            for tag in soup(
                [
                    "script",
                    "style",
                    "nav",
                    "header",
                    "footer",
                    "aside",
                    "title",
                    "caption",
                ]
            ):
                tag.decompose()

            # 텍스트 추출
            text = soup.get_text()

            # 여러 공백을 하나로 치환
            text = re.sub(r"\s+", " ", text)

            # 앞뒤 공백 제거
            text = text.strip()

            return text if text else None

        except Exception as e:
            print(f"URL {url}에서 텍스트 추출 중 오류: {e}")
            return None

    def search_and_extract_text(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        검색을 수행하고 각 결과의 웹페이지에서 텍스트를 추출합니다.

        Args:
            query: 검색할 쿼리
            num_results: 처리할 결과 수

        Returns:
            텍스트가 포함된 검색 결과 리스트
        """
        search_results = self.search(query, num_results)

        for result in search_results:
            print(f"텍스트 추출 중: {result['title']}")
            # HTML 원문 추출
            html = self._fetch_html(result["link"])
            result["extracted_html"] = html
            # 텍스트 추출
            text = self.extract_text_from_html(html)
            print(f"추출된 텍스트: {text}")
            result["extracted_text"] = text

        return search_results

    def _fetch_html(self, url: str) -> str:
        import requests

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"HTML 추출 실패: {e}")
            return ""

    def extract_text_from_html(self, html: str) -> str:
        # 기존 extract_text_from_url에서 html 파싱 부분만 분리해서 사용
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        # 불필요한 태그들 제거
        for tag in soup(
            ["script", "style", "nav", "header", "footer", "aside", "title", "caption"]
        ):
            tag.decompose()

        # 텍스트 추출
        text = soup.get_text(separator=" ", strip=True)

        # 여러 공백을 하나로 치환
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def search_and_extract_law_articles(
        self, query: str, num_results: int = 5
    ) -> List[Dict]:
        """
        검색을 수행하고 추출된 텍스트에서 법령+조항 번호를 찾아냅니다.

        Args:
            query: 검색할 쿼리
            num_results: 처리할 결과 수

        Returns:
            법령+조항 정보가 포함된 검색 결과 리스트
        """
        search_results = self.search_and_extract_text(query, num_results)

        for result in search_results:
            if result.get("extracted_text"):
                print(f"법령+조항 추출 중: {result['title']}")
                articles = extract_law_articles(result["extracted_text"])
                result["law_articles"] = articles
                print(f"  찾은 법령+조항 수: {len(articles)}")
                for article in articles:
                    print(f"    - {article['full_text']}")
            else:
                result["law_articles"] = []

        return search_results

    def get_unique_law_articles(self, search_results: List[Dict]) -> List[Dict]:
        """
        검색 결과에서 중복을 제거한 고유한 법령+조항 목록을 반환합니다.

        Args:
            search_results: search_and_extract_law_articles의 결과

        Returns:
            중복 제거된 법령+조항 목록
        """
        unique_articles = {}

        for result in search_results:
            for article in result.get("law_articles", []):
                key = article["key"]
                if key not in unique_articles:
                    unique_articles[key] = article

        return list(unique_articles.values())

    def search_law_articles_summary(self, query: str, num_results: int = 5) -> Dict:
        """
        검색을 수행하고 법령+조항 정보를 요약하여 반환합니다.

        Args:
            query: 검색할 쿼리
            num_results: 처리할 결과 수

        Returns:
            요약된 법령+조항 정보
        """
        search_results = self.search_and_extract_law_articles(query, num_results)

        # 고유한 법령+조항 목록
        unique_articles = self.get_unique_law_articles(search_results)

        # 법령별로 그룹화
        law_groups = {}
        for article in unique_articles:
            law_name = article["law_name"]
            if law_name not in law_groups:
                law_groups[law_name] = []
            law_groups[law_name].append(article)

        # 각 법령별로 조항 번호 정렬
        for law_name in law_groups:
            law_groups[law_name].sort(key=lambda x: int(x["article_num"]))

        summary = {
            "query": query,
            "total_articles_found": len(unique_articles),
            "total_sources": len(search_results),
            "law_groups": law_groups,
            "all_articles": unique_articles,
            "search_results": search_results,
        }

        return summary


def main():
    """테스트 함수"""
    try:
        searcher = GoogleCSESearch()

        # 테스트 검색
        query = "건축법 제16조"
        print(f"검색 쿼리: {query}")

        results = searcher.search(query, 3)

        for i, result in enumerate(results, 1):
            print(f"\n--- 결과 {i} ---")
            print(f"제목: {result['title']}")
            print(f"링크: {result['link']}")
            print(f"스니펫: {result['snippet']}")

            # 텍스트 추출 테스트
            text = searcher.extract_text_from_url(result["link"])
            if text:
                print(f"추출된 텍스트 (처음 200자): {text[:200]}...")
            else:
                print("텍스트 추출 실패")

    except Exception as e:
        print(f"오류: {e}")


if __name__ == "__main__":
    main()
