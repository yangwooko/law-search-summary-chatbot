#!/usr/bin/env python3
"""
구글 CSE 검색 기능 테스트 스크립트
"""

from google_cse_search import GoogleCSESearch


def test_basic_search():
    """기본 검색 기능 테스트"""
    print("=== 기본 검색 기능 테스트 ===")

    try:
        searcher = GoogleCSESearch()

        # 테스트 쿼리들
        test_queries = [
            "건축법에서 경미한 사항의 변경이란?",
        ]

        for query in test_queries:
            print(f"\n🔍 검색 쿼리: {query}")
            results = searcher.search(query, 3)

            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title']}")
                    print(f"     링크: {result['link']}")
                    print(f"     스니펫: {result['snippet'][:100]}...")
            else:
                print("  검색 결과가 없습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def test_text_extraction():
    """텍스트 추출 기능 테스트"""
    print("\n=== 텍스트 추출 기능 테스트 ===")

    try:
        searcher = GoogleCSESearch()

        # 간단한 검색 수행
        query = "건축법에서 경미한 사항의 변경이란?"
        results = searcher.search(query, 2)

        for i, result in enumerate(results, 1):
            print(f"\n📄 텍스트 추출 테스트 {i}: {result['title']}")
            print(f"   URL: {result['link']}")

            # 텍스트 추출
            text = searcher.extract_text_from_url(result["link"])

            if text:
                print(f"   추출된 텍스트 길이: {len(text)} 문자")
                print(f"   미리보기: {text[:200]}...")
            else:
                print("   텍스트 추출 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def test_search_and_extract():
    """검색과 텍스트 추출 통합 테스트"""
    print("\n=== 검색 및 텍스트 추출 통합 테스트 ===")

    try:
        searcher = GoogleCSESearch()

        query = "건축법에서 경미한 사항의 변경이란?"
        print(f"🔍 검색 쿼리: {query}")

        # 검색 및 텍스트 추출
        results = searcher.search_and_extract_text(query, 2)

        for i, result in enumerate(results, 1):
            print(result)
            print(f"\n📄 결과 {i}: {result['title']}")
            print(f"   링크: {result['link']}")

            if result.get("extracted_text"):
                text = result["extracted_text"]
                print(f"   추출된 텍스트 길이: {len(text)} 문자")
                print(f"   미리보기: {text[:300]}...")
            else:
                print("   텍스트 추출 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def test_law_articles_extraction():
    """법령+조항 추출 테스트"""
    print("\n=== 법령+조항 추출 테스트 ===")

    try:
        searcher = GoogleCSESearch()

        query = "건축법에서 경미한 사항의 변경이란?"
        print(f"🔍 검색 쿼리: {query}")

        # 검색 및 법령+조항 추출
        results = searcher.search_and_extract_law_articles(query, 2)

        total_articles = 0
        for i, result in enumerate(results, 1):
            print(f"\n📄 결과 {i}: {result['title']}")

            articles = result.get("law_articles", [])
            total_articles += len(articles)

            if articles:
                print(f"   찾은 법령+조항 ({len(articles)}개):")
                for article in articles:
                    # print(f"     - {article['full_text']}")
                    print(f"{article['law_name']}||{article['article_num']}")
            else:
                print("   찾은 법령+조항 없음")

        print(f"\n총 {total_articles}개의 법령+조항을 찾았습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """메인 테스트 함수"""
    print("🚀 구글 CSE 검색 기능 테스트 시작\n")

    # # 1. 기본 검색 테스트
    # test_basic_search()

    # # 2. 텍스트 추출 테스트
    # test_text_extraction()

    # # 3. 통합 테스트
    # test_search_and_extract()

    # 4. 법령+조항 추출 테스트
    test_law_articles_extraction()

    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
