# 법령 검색 및 조문 내용 가져오기 시스템

Tavily API와 법제처 OpenAPI를 활용하여 법령 관련 정보를 검색하고, 텍스트에서 법령명과 조문번호를 자동으로 추출하여 해당 조문의 실제 내용을 가져오는 Python 프로젝트입니다.

## 주요 기능

### 1. 통합 검색 시스템 (`law_search_integrated.py`)
- **Tavily API 검색**: 법령 사이트에서 관련 정보 검색
- **Crawl4AI 크롤링**: 검색 결과 URL들을 크롤링하여 텍스트 추출
- **법령 추출**: 크롤링된 텍스트에서 법령명과 조문번호 자동 추출
- **조문 내용 가져오기**: 법제처 API를 통해 실제 조문 내용 조회

### 2. 법령+조항 추출 (`law_article_extractor.py`)
- 정규표현식 기반 법령명+조문번호 패턴 매칭
- 다양한 법령 유형 지원:
  - 법률 (예: 건축법)
  - 법률 시행령 (예: 건축법 시행령)
  - 법률 시행규칙 (예: 건축법 시행규칙)
  - 조례, 규칙
  - 부칙, 별표, 별지
- 중복 제거 및 후처리 로직

### 3. 법령 조문 내용 가져오기 (`law_content_fetcher.py`)
- **법령 ID 조회**: 법령명으로 법제처 API에서 법령 ID 검색
- **조문 내용 조회**: 법령 ID와 조문번호로 실제 조문 내용 가져오기
- **텍스트 포매팅**: JSON 형태의 조문 내용을 읽기 쉬운 텍스트로 변환

## 설치 및 설정

### 1. 의존성 설치
```bash
uv sync
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# Tavily API 설정 (검색용)
TAVILY_API_KEY=your_tavily_api_key_here

# 법제처 OpenAPI 설정 (법령 조문 내용 가져오기용)
LAW_API_KEY=your_law_api_key_here
```

### 3. API 키 발급
- **Tavily API**: [Tavily AI](https://tavily.com/)에서 무료 API 키 발급
- **법제처 OpenAPI**: [국가법령정보센터](https://www.law.go.kr/)에서 OpenAPI 키 발급

## 사용법

### 1. 통합 검색 및 조문 내용 가져오기
```python
from law_search_integrated import LawSearchIntegrated

# 통합 검색 시스템 초기화
searcher = LawSearchIntegrated()

# 사용자 질문으로 검색 → 크롤링 → 법령 추출 → 조문 내용 가져오기
results = await searcher.crawl_and_extract_laws(
    "건축법에서 경미한 사항의 변경이란?", 
    domains=["law.go.kr"], 
    num_results=3
)

# 결과 포맷팅
formatted_output = searcher.format_results(results)
print(formatted_output)
```

### 2. 법령명+조문번호 추출
```python
from law_article_extractor import extract_law_articles

text = "건축법 제12조에 따르면 건축허가를 받아야 한다."
articles = extract_law_articles(text)
# 결과: [{'law_name': '건축법', 'article_num': '12', ...}]
```

### 3. 조문 내용 직접 가져오기
```python
from law_content_fetcher import LawContentFetcher

fetcher = LawContentFetcher()
content = await fetcher.get_law_article_content("건축법", "16")
print(content)
```

## 실행 예시

```bash
# 통합 시스템 테스트
python law_search_integrated.py
```

### 출력 예시
```
=== 통합 법령 검색 시스템 ===

사용자 질문: 건축법에서 경미한 사항의 변경이란?

🔍 검색 시작: '건축법에서 경미한 사항의 변경이란?'
🔍 지정된 도메인에서 검색: law.go.kr
📄 3개의 URL을 크롤링합니다.
📝 크롤링 완료: 6524 문자
🔍 법령명과 조문번호 추출 중...
📋 추출된 법령: 1개
  1. 건축법 시행령 제12조
📖 조문 내용 가져오기 중...

# 검색 결과: '건축법에서 경미한 사항의 변경이란?'

## 📋 발견된 법령 (1개)
1. **건축법 시행령** 제12조

## 📖 조문 내용
### 1. 건축법 시행령 제12조
**제목**: 허가·신고사항의 변경 등
**내용**:
① 법 제16조제1항에 따라 허가를 받았거나 신고한 사항을 변경하려면...
```

## 지원하는 법령 패턴

1. **기본 법률**: `건축법 제12조`
2. **시행령**: `건축법 시행령 제14조`
3. **시행규칙**: `건축법 시행규칙 제7조`
4. **조례/규칙**: `서울특별시조례 제123조`
5. **부칙/별표/별지**: `부칙 제1조`, `별표 1`, `별지 2`
6. **대괄호 부가정보**: `건축법[시행 2024.1.1] 제16조`

## 프로젝트 구조

```
law-search-summary-chatbot/
├── law_search_integrated.py    # 통합 검색 시스템 (메인)
├── law_content_fetcher.py      # 법령 조문 내용 가져오기
├── law_article_extractor.py    # 법령명+조문번호 추출
├── references/                 # 참조 파일들
├── pyproject.toml             # 프로젝트 설정
├── uv.lock                    # 의존성 잠금 파일
├── README.md                  # 프로젝트 문서
├── plan.md                    # 개발 계획
└── env.example                # 환경 변수 예제
```

## 주요 특징

### 🔍 검색 기능
- **Tavily API**: 안정적이고 정확한 검색 결과
- **도메인 지정**: 법령 사이트만 검색하여 관련성 높은 결과
- **크롤링**: 검색 결과의 실제 내용을 텍스트로 추출

### 📋 법령 추출
- **정확한 패턴 매칭**: 다양한 법령 유형 지원
- **중복 제거**: 동일한 법령+조항의 중복 추출 방지
- **후처리**: 불필요한 텍스트 제거 및 정규화

### 📖 조문 내용
- **실시간 조회**: 법제처 API를 통한 최신 조문 내용
- **구조화된 포매팅**: 항, 호, 목 구조를 유지한 읽기 쉬운 텍스트
- **중복 번호 제거**: 깔끔한 텍스트 출력

## 개발 과정

### 주요 개선사항
1. **검색 엔진 변경**: Google CSE → Tavily API로 변경하여 안정성 향상
2. **크롤링 통합**: Crawl4AI를 활용한 효율적인 웹 크롤링
3. **법령 내용 API**: 법제처 OpenAPI를 통한 실제 조문 내용 조회
4. **텍스트 포매팅**: JSON → 읽기 쉬운 텍스트 변환
5. **통합 시스템**: 검색부터 조문 내용까지 완전 자동화

### 해결된 문제들
- 구글 봇 차단 문제 → Tavily API 사용
- 검색 결과의 링크 제거 → Crawl4AI 설정 활용
- 조문 내용의 중복 번호 → 포매팅 로직 개선
- 크롤링 결과 처리 → `_results` 구조 분석

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 