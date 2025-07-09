import os
import requests
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import time
from bs4 import BeautifulSoup
import re
from law_article_extractor import extract_law_articles
import random


class GoogleSearch:
    """일반 구글 검색을 위한 클래스 (fallback용)"""

    def __init__(self):
        self.base_url = "https://www.google.com/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        일반 구글 검색을 수행합니다.

        Args:
            query: 검색할 쿼리
            num_results: 반환할 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            params = {
                "q": query,
                "num": min(num_results, 10),
                "hl": "ko",
                "gl": "kr",
            }

            response = requests.get(
                self.base_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()

            # HTML 파싱
            soup = BeautifulSoup(response.content, "html.parser")

            results = []

            # 구글 검색 결과 파싱 - 다양한 클래스명 시도
            search_results = []

            # 여러 가능한 클래스명으로 검색
            possible_classes = ["g", "rc", "result", "search-result"]
            for class_name in possible_classes:
                results = soup.find_all("div", class_=class_name)
                if results:
                    search_results = results
                    break

            # 여전히 결과가 없으면 다른 방법 시도
            if not search_results:
                # h3 태그를 가진 div 찾기
                search_results = soup.find_all("div")
                search_results = [div for div in search_results if div.find("h3")]

            for result in search_results[:num_results]:
                try:
                    # 제목과 링크 추출
                    title_element = result.find("h3")
                    if not title_element:
                        continue

                    title = str(title_element.get_text(strip=True))

                    # 링크 추출 - 여러 방법 시도
                    link = ""
                    link_element = result.find("a")
                    if link_element:
                        link = str(link_element.get("href", ""))

                    # 링크가 상대 경로인 경우 처리
                    if link.startswith("/url?q="):
                        from urllib.parse import unquote

                        link = unquote(link.split("/url?q=")[1].split("&")[0])

                    if not link or not link.startswith("http"):
                        continue

                    # 스니펫 추출 - 여러 클래스명 시도
                    snippet = ""
                    snippet_classes = ["VwiC3b", "snippet", "description", "summary"]
                    for snippet_class in snippet_classes:
                        snippet_element = result.find("div", class_=snippet_class)
                        if snippet_element:
                            snippet = str(snippet_element.get_text(strip=True))
                            break

                    # 여전히 스니펫이 없으면 p 태그에서 찾기
                    if not snippet:
                        p_element = result.find("p")
                        if p_element:
                            snippet = str(p_element.get_text(strip=True))

                    # 도메인 추출
                    from urllib.parse import urlparse

                    domain = urlparse(link).netloc

                    results.append(
                        {
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "displayLink": domain,
                        }
                    )

                except Exception as e:
                    print(f"결과 파싱 중 오류: {e}")
                    continue

            return results

        except Exception as e:
            print(f"일반 구글 검색 중 오류 발생: {e}")
            return []

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
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
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


class GoogleCSESearch:
    """구글 Custom Search Engine을 사용한 웹 검색 클래스"""

    def __init__(self, use_fallback: bool = True):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_CSE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        self.use_fallback = use_fallback

        # fallback용 일반 구글 검색 객체
        self.fallback_searcher = GoogleSearch() if use_fallback else None

        # CSE 설정이 없고 fallback이 활성화된 경우 경고만 출력
        if not self.api_key or not self.cse_id:
            if use_fallback:
                print("⚠️  CSE 설정이 없습니다. 일반 구글 검색을 사용합니다.")
            else:
                raise ValueError(
                    "GOOGLE_CSE_API_KEY와 GOOGLE_CSE_ID가 .env 파일에 설정되어야 합니다."
                )

        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        구글 CSE로 검색을 수행합니다. 실패 시 일반 구글 검색으로 fallback합니다.

        Args:
            query: 검색할 쿼리
            num_results: 반환할 결과 수 (최대 10개)

        Returns:
            검색 결과 리스트
        """
        # CSE 설정이 있으면 CSE 사용
        if self.api_key and self.cse_id:
            try:
                return self._search_with_cse(query, num_results)
            except Exception as e:
                print(f"CSE 검색 실패: {e}")
                if self.use_fallback:
                    print("일반 구글 검색으로 fallback합니다.")
                    return self._search_with_fallback(query, num_results)
                else:
                    return []
        else:
            # CSE 설정이 없으면 fallback 사용
            if self.use_fallback:
                return self._search_with_fallback(query, num_results)
            else:
                return []

    def _search_with_cse(self, query: str, num_results: int = 10) -> List[Dict]:
        """CSE를 사용한 검색"""
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10),  # 구글 CSE는 한 번에 최대 10개 결과
        }

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

    def _search_with_fallback(self, query: str, num_results: int = 10) -> List[Dict]:
        """일반 구글 검색을 사용한 fallback"""
        return self.fallback_searcher.search(query, num_results)

    def search_with_pagination(self, query: str, total_results: int = 20) -> List[Dict]:
        """
        페이지네이션을 사용하여 더 많은 검색 결과를 가져옵니다.

        Args:
            query: 검색할 쿼리
            total_results: 총 가져올 결과 수

        Returns:
            검색 결과 리스트
        """
        # CSE 설정이 있으면 CSE 사용
        if self.api_key and self.cse_id:
            try:
                return self._search_with_pagination_cse(query, total_results)
            except Exception as e:
                print(f"CSE 페이지네이션 검색 실패: {e}")
                if self.use_fallback:
                    print("일반 구글 검색으로 fallback합니다.")
                    return self._search_with_pagination_fallback(query, total_results)
                else:
                    return []
        else:
            # CSE 설정이 없으면 fallback 사용
            if self.use_fallback:
                return self._search_with_pagination_fallback(query, total_results)
            else:
                return []

    def _search_with_pagination_cse(
        self, query: str, total_results: int = 20
    ) -> List[Dict]:
        """CSE를 사용한 페이지네이션 검색"""
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

        return all_results[:total_results]

    def _search_with_pagination_fallback(
        self, query: str, total_results: int = 20
    ) -> List[Dict]:
        """일반 구글 검색을 사용한 페이지네이션 fallback"""
        # 일반 구글 검색은 페이지네이션을 지원하지 않으므로 단일 검색으로 대체
        return self.fallback_searcher.search(query, total_results)

    def extract_text_from_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        URL에서 텍스트를 추출합니다.

        Args:
            url: 텍스트를 추출할 URL
            timeout: 요청 타임아웃 (초)

        Returns:
            추출된 텍스트 또는 None
        """
        # CSE 설정이 있으면 CSE 방식 사용, 없으면 fallback 방식 사용
        if self.api_key and self.cse_id:
            return self._extract_text_from_url_cse(url, timeout)
        else:
            return self.fallback_searcher.extract_text_from_url(url, timeout)

    def _extract_text_from_url_cse(self, url: str, timeout: int = 10) -> Optional[str]:
        """CSE 방식의 텍스트 추출"""
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
