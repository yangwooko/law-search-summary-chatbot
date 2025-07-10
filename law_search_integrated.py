import asyncio
import os
import time
import re
from typing import List, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from tavily import TavilyClient
from dotenv import load_dotenv

# LLM용
from openai import OpenAI

# 로컬 모듈 import
from law_article_extractor import (
    extract_law_articles,
    extract_all_articles_with_references,
    extract_referenced_articles,
)
from law_content_fetcher import LawContentFetcher

load_dotenv()


class LawSearchIntegrated:
    """통합 법령 검색 및 조문 내용 가져오기 클래스"""

    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.law_fetcher = LawContentFetcher()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL")
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

    def tavily_search(
        self, query: str, domains: List[str] | None = None, num_results: int = 5
    ) -> List[str]:
        """Tavily API를 사용하여 검색 결과 가져오기"""
        try:
            if not self.tavily_api_key:
                print("⚠️  TAVILY_API_KEY 환경변수가 설정되지 않았습니다.")
                return []

            client = TavilyClient(api_key=self.tavily_api_key)

            # 검색 파라미터 설정
            search_params = {
                "query": query,
                "search_depth": "basic",
                "max_results": num_results,
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False,
            }

            # 도메인 지정이 있으면 추가
            if domains:
                search_params["include_domains"] = domains
                print(f"🔍 지정된 도메인에서 검색: {', '.join(domains)}")

            response = client.search(**search_params)

            urls = []
            if "results" in response:
                for result in response["results"]:
                    if "url" in result:
                        urls.append(result["url"])

            return urls

        except Exception as e:
            print(f"Tavily 검색 중 오류: {e}")
            return []

    def clean_markdown_text(self, text: str) -> str:
        """마크다운 텍스트에서 URL 링크 제거"""
        if not text:
            return text

        # 마크다운 링크 패턴 제거: [텍스트](URL) -> 텍스트
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # 일반 URL 패턴 제거: http://... 또는 https://...
        text = re.sub(r"https?://[^\s\)\]\>]+", "", text)

        # 이미지 링크 제거: ![alt](URL)
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)

        # 빈 줄 정리
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        # 앞뒤 공백 제거
        text = text.strip()

        return text

    async def crawl_and_extract_laws(
        self, query: str, domains: List[str] | None = None, num_results: int = 5
    ) -> Dict[str, Any]:
        """검색 → 크롤링 → 법령 추출 → 조문 내용 가져오기 + LLM 답변"""

        print(f"🔍 검색 시작: '{query}'")

        # 1. Tavily 검색으로 URL 수집
        urls = self.tavily_search(query, domains, num_results)

        if not urls:
            return {
                "success": False,
                "error": "검색 결과를 가져올 수 없습니다. Tavily API 키를 확인해주세요.",
                "search_query": query,
                "crawled_content": "",
                "extracted_laws": [],
                "law_contents": [],
                "llm_answer": None,
            }

        print(f"📄 {len(urls)}개의 URL을 크롤링합니다.")

        # 2. 크롤링하여 텍스트 수집
        all_text = ""

        # 링크 제거를 위한 CrawlerRunConfig 설정
        config = CrawlerRunConfig(
            exclude_external_links=True,
            exclude_internal_links=True,
            exclude_social_media_links=True,
            exclude_all_images=True,
        )

        # Crawl4AI 로그 출력 억제
        import logging
        import sys

        # 모든 로그 레벨을 ERROR로 설정
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger("crawl4ai").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("requests").setLevel(logging.ERROR)

        # 표준 출력 리다이렉션 (임시)
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            for i, url in enumerate(urls, 1):
                try:
                    print(f"크롤링 중 ({i}/{len(urls)}): {url}")
                    result = await crawler.arun(url=url, config=config)

                    # result 처리 - CrawlResultContainer._results 내부 접근
                    try:
                        markdown_content = None
                        # _results 안전 접근
                        results_list = None
                        if isinstance(result, dict) and "_results" in result:
                            results_list = result["_results"]
                        else:
                            results_list = getattr(result, "_results", None)
                        if results_list and isinstance(results_list, list):
                            for item in results_list:
                                item_dict = item
                                if not isinstance(item, dict) and hasattr(
                                    item, "__dict__"
                                ):
                                    item_dict = item.__dict__
                                if isinstance(item_dict, dict):
                                    for key in ["markdown", "content", "text"]:
                                        if key in item_dict and item_dict[key]:
                                            markdown_content = item_dict[key]
                                            break
                                if not markdown_content:
                                    for key in ["markdown", "content", "text"]:
                                        val = getattr(item, key, None)
                                        if val:
                                            markdown_content = val
                                            break
                                if markdown_content:
                                    break
                        if markdown_content:
                            cleaned_text = self.clean_markdown_text(markdown_content)
                            all_text += f"\n\n--- {url} ---\n\n{cleaned_text}"
                            # print(f"DEBUG: 텍스트 추출 성공, 길이: {len(cleaned_text)}")
                        else:
                            print(f"크롤링 결과에서 텍스트를 추출할 수 없습니다: {url}")
                    except Exception as e:
                        print(f"결과 처리 중 오류: {e}")
                        continue

                except Exception as e:
                    print(f"크롤링 실패 ({url}): {e}")
                    continue

                # 요청 간격 조절
                time.sleep(1)

        # 표준 출력 복원
        sys.stdout.close()
        sys.stdout = original_stdout

        if not all_text.strip():
            return {
                "success": False,
                "error": "크롤링된 내용이 없습니다.",
                "search_query": query,
                "crawled_content": "",
                "extracted_laws": [],
                "law_contents": [],
                "llm_answer": None,
            }

        print(f"📝 크롤링 완료: {len(all_text)} 문자")

        # 3. 법령명과 조문번호 추출 (직접 언급 + 참조)
        print("🔍 법령명과 조문번호 추출 중...")

        # 첫 번째로 발견된 법령명을 기준으로 참조 조항도 추출
        initial_laws = extract_law_articles(all_text)
        current_law_name = None
        if initial_laws:
            current_law_name = initial_laws[0]["law_name"]
            print(f"📋 기준 법령: {current_law_name}")

        # 직접 언급된 조항과 참조 조항 모두 추출
        all_extracted = extract_all_articles_with_references(all_text, current_law_name)
        extracted_laws = all_extracted["all_articles"]
        direct_laws = all_extracted["direct_articles"]
        referenced_laws = all_extracted["referenced_articles"]

        print(
            f"📋 추출된 법령: {len(extracted_laws)}개 (직접: {len(direct_laws)}개, 참조: {len(referenced_laws)}개)"
        )
        for i, law in enumerate(direct_laws, 1):
            print(f"  {i}. {law['law_name']} 제{law['article_num']}조 (직접 언급)")
        for i, law in enumerate(referenced_laws, 1):
            print(
                f"  {len(direct_laws) + i}. {law['law_name']} 제{law['article_num']}조 (참조)"
            )

        # 4. 추출된 법령의 조문 내용 가져오기
        law_contents = []
        if extracted_laws:
            print("📖 조문 내용 가져오기 중...")
            # print(f"DEBUG: extracted_laws: {extracted_laws}")
            law_contents = await self.law_fetcher.fetch_law_articles_content(
                extracted_laws
            )

            # 5. 조문 내용에서 추가 참조 조항 추출
            additional_references = []
            for content_result in law_contents:
                if (
                    content_result.get("content", {}).get("success")
                    and current_law_name
                ):
                    content_text = content_result["content"]["content"].get(
                        "content", ""
                    )
                    if content_text:
                        # 조문 내용에서 참조 추출
                        content_refs = extract_referenced_articles(
                            content_text, current_law_name
                        )
                        additional_references.extend(content_refs)

            # 중복 제거
            unique_additional_refs = []
            seen_keys = set()
            for ref in additional_references:
                if ref["key"] not in seen_keys:
                    unique_additional_refs.append(ref)
                    seen_keys.add(ref["key"])

            if unique_additional_refs:
                print(
                    f"📋 조문 내용에서 추가 참조 발견: {len(unique_additional_refs)}개"
                )
                for ref in unique_additional_refs:
                    print(f"  - {ref['law_name']} 제{ref['article_num']}조")

                # 추가 참조 조항을 referenced_laws에 합치기
                referenced_laws.extend(unique_additional_refs)

                # 추가 참조 조항의 내용도 가져오기
                additional_contents = await self.law_fetcher.fetch_law_articles_content(
                    unique_additional_refs
                )
                law_contents.extend(additional_contents)

        # 6. RAG용 context 생성 (크롤링+법령 내용)
        rag_context = all_text
        for law in law_contents:
            if law.get("content", {}).get("success"):
                c = law["content"]["content"].get("content", "")
                if c:
                    rag_context += f"\n\n--- 법령 조문 ---\n\n{c}"

        # 7. LLM 답변 생성
        llm_answer = None
        if self.openai_client:
            try:
                prompt = f"""
아래는 법령 및 관련 조문 내용입니다. 이 내용을 참고하여 사용자의 질문에 대해 법적 근거와 함께 명확하게 답변해 주세요. 답변은 최대한 법령 내용을 인용하는 방식으로 작성해주세요.

[법령 및 조문]
{rag_context}

[질문]
{query}

[답변]
"""
                model_name = self.openai_model or "gpt-3.5-turbo-16k"
                response = self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "당신은 법률 전문가입니다."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=800,
                )
                llm_answer = (
                    response.choices[0].message.content.strip()
                    if response.choices[0].message.content
                    else None
                )
                # print(f"DEBUG: LLM 답변: {llm_answer}")
            except Exception as e:
                print(f"LLM 답변 생성 오류: {e}")
                llm_answer = None

        return {
            "success": True,
            "search_query": query,
            "crawled_content": (
                all_text[:2000] + "..." if len(all_text) > 2000 else all_text
            ),
            "extracted_laws": extracted_laws,
            "direct_laws": direct_laws,
            "referenced_laws": referenced_laws,
            "law_contents": law_contents,
            "llm_answer": llm_answer,
        }

    def get_law_domains(self) -> List[str]:
        """법령 관련 도메인 목록 반환"""
        return [
            "law.go.kr",  # 국가법령정보센터
            # "casenote.kr",  # 케이스노트
            # "bigcase.ai",  # 빅케이스
            # "scourt.go.kr",  # 대법원
            # "klaw.go.kr",  # 한국법제연구원
        ]

    def get_news_domains(self) -> List[str]:
        """뉴스 관련 도메인 목록 반환"""
        return [
            "news.naver.com",  # 네이버 뉴스
            # "news.daum.net",  # 다음 뉴스
            # "news.khan.co.kr",  # 경향신문
            # "chosun.com",  # 조선일보
            # "joongang.co.kr",  # 중앙일보
        ]

    def format_results(self, results: Dict[str, Any]) -> str:
        """결과를 보기 좋게 포맷팅"""
        if not results.get("success"):
            return f"❌ 오류: {results.get('error', '알 수 없는 오류')}"

        output = f"# 검색 결과: '{results['search_query']}'\n\n"

        # 추출된 법령 요약
        direct_laws = results.get("direct_laws", [])
        referenced_laws = results.get("referenced_laws", [])
        all_laws = results.get("extracted_laws", [])

        if all_laws:
            output += f"## 📋 발견된 법령 ({len(all_laws)}개)\n\n"

            # 직접 언급된 법령
            if direct_laws:
                output += "### 직접 언급된 법령\n\n"
                for i, law in enumerate(direct_laws, 1):
                    output += f"{i}. **{law['law_name']}** 제{law['article_num']}조\n"
                output += "\n"

            # 참조된 법령
            if referenced_laws:
                output += "### 참조된 법령\n\n"
                for i, law in enumerate(referenced_laws, 1):
                    ref_type = law.get("reference_type", "참조")
                    output += f"{i}. **{law['law_name']}** 제{law['article_num']}조 ({ref_type})\n"
                output += "\n"

        # # 조문 내용
        # law_contents = results.get("law_contents", [])
        # if law_contents:
        #     output += "## 📖 조문 내용\n\n"
        #     for i, result in enumerate(law_contents, 1):
        #         original = result["original_article"]
        #         content = result["content"]

        #         print(f"DEBUG: top level content: {content}")

        #         output += (
        #             f"### {i}. {original['law_name']} 제{original['article_num']}조\n\n"
        #         )

        #         if content.get("success"):
        #             content_data = content.get("content", {})
        #             title = content_data.get("title", "제목 없음")
        #             law_content = content_data.get("content", "내용 없음")

        #             output += f"**제목**: {title}\n\n"
        #             output += f"**내용**:\n{law_content}\n\n"
        #         else:
        #             output += (
        #                 f"❌ **오류**: {content.get('error', '알 수 없는 오류')}\n\n"
        #             )

        #         output += "---\n\n"
        # else:
        #     output += "## 📖 조문 내용\n\n❌ 조문 내용을 가져올 수 없습니다.\n\n"

        # LLM 답변
        llm_answer = results.get("llm_answer")
        if llm_answer:
            output += "## 🤖 LLM 답변\n\n"
            output += llm_answer.strip() + "\n\n"

        return output


async def main():
    """테스트 함수"""
    print("=== 통합 법령 검색 시스템 ===\n")

    # 사용자 입력 시뮬레이션
    user_query = "건축법에서 경미한 사항의 변경이란?"

    print(f"사용자 질문: {user_query}\n")

    # 통합 검색 실행
    searcher = LawSearchIntegrated()

    # 법령 사이트에서 검색
    law_domains = searcher.get_law_domains()
    results = await searcher.crawl_and_extract_laws(user_query, law_domains, 3)

    # 결과 출력
    formatted_output = searcher.format_results(results)
    print(formatted_output)


if __name__ == "__main__":
    asyncio.run(main())
