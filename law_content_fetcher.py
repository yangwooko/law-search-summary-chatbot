import os
import re
import json
import urllib.parse
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class LawContentFetcher:
    """법령 조문 내용을 가져오는 클래스"""

    def __init__(self):
        self.LAW_ACCESS_OC = os.getenv("LAW_API_KEY", "YOUR_LAW_API_KEY")
        self.base_url = "https://www.law.go.kr"

    async def get_law_article_content(
        self, law_name: str, article_num: str
    ) -> Dict[str, Any]:
        """법령명과 조문번호로 해당 조문의 내용을 가져오기"""
        try:
            # API 키 확인
            if self.LAW_ACCESS_OC == "YOUR_LAW_API_KEY":
                return {"error": "LAW_API_KEY 환경변수가 설정되지 않았습니다."}

            # 1. 법령명으로 일련번호(ID) 조회
            law_id = await self._get_law_id(law_name)
            if not law_id:
                return {"error": f"법령 ID를 찾을 수 없습니다: {law_name}"}

            # 2. 조문번호를 6자리 형식으로 변환
            jo_num = self._convert_article_to_jo_num(article_num)

            # 3. 조문 API 호출
            law_content = await self._get_law_article_by_id(law_id, jo_num)
            if not law_content:
                return {
                    "error": f"조문 정보를 찾을 수 없습니다: {law_name} 제{article_num}조"
                }

            return {
                "law_name": law_name,
                "article_num": article_num,
                "content": law_content,
                "success": True,
            }

        except Exception as e:
            return {"error": f"법령 내용 가져오기 오류: {str(e)}"}

    async def _get_law_id(self, law_name: str) -> Optional[str]:
        """법령명으로 법령 ID 조회"""
        try:
            search_url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={self.LAW_ACCESS_OC}&target=law&type=JSON&query={urllib.parse.quote(law_name)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as resp:
                    if resp.status != 200:
                        print(f"API 호출 실패: {resp.status} - {search_url}")
                        return None

                    # Content-Type 확인
                    content_type = resp.headers.get("content-type", "")
                    if "application/json" not in content_type:
                        print(f"JSON이 아닌 응답: {content_type}")
                        return None

                    search_data = await resp.json()

            # JSON 구조에서 일련번호(ID) 추출
            if search_data and isinstance(search_data, dict):
                for k in search_data:
                    if k.startswith("law") and isinstance(search_data[k], dict):
                        # 법령ID(6자리) 또는 법령일련번호(6~7자리) 모두 가능
                        law_id = search_data[k].get("법령ID") or search_data[k].get(
                            "법령일련번호"
                        )
                        if law_id:
                            return law_id

            # XML fallback (JSON이 비어있을 때)
            search_url_xml = f"https://www.law.go.kr/DRF/lawSearch.do?OC={self.LAW_ACCESS_OC}&target=law&type=XML&query={urllib.parse.quote(law_name)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url_xml) as resp:
                    if resp.status != 200:
                        return None

                    xml_text = await resp.text()

            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_text)

            for law_elem in root.findall("law"):
                id_elem = law_elem.find("법령ID")
                if id_elem is not None:
                    return id_elem.text

            return None

        except Exception as e:
            print(f"법령 ID 조회 오류: {e}")
            return None

    def _convert_article_to_jo_num(self, article_num: str) -> str:
        """조문번호를 6자리 형식으로 변환"""
        try:
            if not article_num:
                return "000100"  # 기본 1조

            # 이미 추출된 조항 번호에서 숫자만 추출
            num = re.sub(r"[^0-9]", "", article_num)
            if not num:
                return "000100"  # 기본 1조

            # 4자리로 패딩하고 맨 아래 2자리는 00으로 채움 (예: 16 -> 001600, 1 -> 000100)
            jo_num = f"{int(num):04d}00"
            return jo_num

        except Exception as e:
            print(f"조문번호 변환 오류: {e}")
            return "000100"

    def _format_law_content(self, content_data: List[Dict]) -> str:
        """JSON 형태의 조문 내용을 읽기 쉬운 텍스트로 포매팅"""
        if not content_data:
            return "내용 없음"

        formatted_text = ""

        for item in content_data:
            # 항번호와 항내용
            hang_num = item.get("항번호", "").strip()
            hang_content = item.get("항내용", "").strip()

            if hang_num and hang_content:
                # 항번호가 이미 항내용에 포함되어 있으면 제거
                if hang_content.startswith(hang_num):
                    formatted_text += f"{hang_content}\n\n"
                else:
                    formatted_text += f"{hang_num}{hang_content}\n\n"

            # 호가 있는 경우
            if "호" in item and item["호"]:
                for ho in item["호"]:
                    ho_num = ho.get("호번호", "").strip()
                    ho_content = ho.get("호내용", "").strip()

                    if ho_num and ho_content:
                        # 호번호가 이미 호내용에 포함되어 있으면 제거
                        if ho_content.startswith(ho_num):
                            formatted_text += f"  {ho_content}\n\n"
                        else:
                            formatted_text += f"  {ho_num}{ho_content}\n\n"

                    # 목이 있는 경우
                    if "목" in ho and ho["목"]:
                        for mok in ho["목"]:
                            mok_num = mok.get("목번호", "").strip()
                            mok_content = mok.get("목내용", "").strip()

                            if mok_num and mok_content:
                                # 목번호가 이미 목내용에 포함되어 있으면 제거
                                if mok_content.startswith(mok_num):
                                    formatted_text += f"    {mok_content}\n\n"
                                else:
                                    formatted_text += f"    {mok_num}{mok_content}\n\n"

        return formatted_text.strip()

    async def _get_law_article_by_id(self, law_id: str, jo_num: str) -> Optional[Dict]:
        """법령 ID와 조문번호로 조문 내용 조회"""
        try:
            law_url = f"https://www.law.go.kr/DRF/lawService.do?OC={self.LAW_ACCESS_OC}&target=lawjosub&type=JSON&ID={law_id}&JO={jo_num}"

            async with aiohttp.ClientSession() as session:
                async with session.get(law_url) as resp:
                    if resp.status != 200:
                        print(f"조문 API 호출 실패: {resp.status}")
                        return None

                    law_data = await resp.json()

            if not law_data or "법령" not in law_data or "조문" not in law_data["법령"]:
                return None

            basic = law_data["법령"].get("기본정보", {})
            jo = law_data["법령"]["조문"].get("조문단위", {})

            # 조문 내용을 텍스트로 포매팅
            content_data = jo.get("항", [])
            formatted_content = self._format_law_content(content_data)

            return {
                "title": jo.get("조문제목", ""),
                "law_name": basic.get("법령명_한글", ""),
                "content": formatted_content,
                "url": law_url,
            }

        except Exception as e:
            print(f"조문 내용 조회 오류: {e}")
            return None

    async def fetch_law_articles_content(self, articles: List[Dict]) -> List[Dict]:
        """extract_law_articles 결과에서 법령 내용을 가져오기"""
        results = []

        for article in articles:
            law_name = article.get("law_name", "")
            article_num = article.get("article_num", "")

            if law_name and article_num:
                print(f"🔍 법령 내용 조회 중: {law_name} 제{article_num}조")
                content = await self.get_law_article_content(law_name, article_num)
                results.append({"original_article": article, "content": content})
            else:
                results.append(
                    {
                        "original_article": article,
                        "content": {"error": "법령명 또는 조문번호가 없습니다."},
                    }
                )

        return results


async def main():
    """테스트 함수"""
    from law_article_extractor import extract_law_articles

    # 테스트용 텍스트
    test_text = """
    건축법 제16조에 따르면 건축주는 건축공사를 착수하기 전까지 건설부령이 정하는 바에 의하여 
    시장·군수·구청장에게 그 공사계획을 신고하여야 한다. 
    건축법 시행령 제12조에서는 허가·신고사항의 변경 등에 대해 규정하고 있다.
    """

    print("=== 법령 조문 내용 가져오기 테스트 ===\n")

    # 1. 법령+조항 추출
    print("1️⃣ 법령+조항 추출")
    articles = extract_law_articles(test_text)
    print(f"추출된 법령+조항: {len(articles)}개")

    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article['law_name']} 제{article['article_num']}조")

    if not articles:
        print("❌ 추출된 법령+조항이 없습니다.")
        return

    print("\n" + "=" * 50 + "\n")

    # 2. 법령 내용 가져오기
    print("2️⃣ 법령 내용 가져오기")
    fetcher = LawContentFetcher()
    results = await fetcher.fetch_law_articles_content(articles)

    for i, result in enumerate(results, 1):
        original = result["original_article"]
        content = result["content"]

        print(f"\n📄 {i}. {original['law_name']} 제{original['article_num']}조")

        if content.get("success"):
            print(f"   제목: {content.get('content', {}).get('title', 'N/A')}")
            print(
                f"   내용: {content.get('content', {}).get('content', 'N/A')[:200]}..."
            )
        else:
            print(f"   ❌ 오류: {content.get('error', '알 수 없는 오류')}")


if __name__ == "__main__":
    asyncio.run(main())
