# 법령 검색 및 조문 내용 + LLM 답변 시스템

Tavily API, 법제처 OpenAPI, OpenAI LLM을 활용하여 법령 관련 정보를 검색·크롤링하고, 텍스트에서 법령명과 조문번호를 자동 추출, 실제 조문 내용과 LLM 기반 답변까지 제공하는 Python 프로젝트입니다.

## 주요 기능

### 1. 통합 검색 + LLM 답변 (`law_search_integrated.py`)
- **Tavily API**로 법령 사이트 검색
- **Crawl4AI**로 검색 결과 URL 크롤링(진행 메시지 억제)
- **법령명+조문번호 자동 추출** (본문/조문 내 참조까지)
- **조문 내용 자동 조회** (법제처 OpenAPI)
- **RAG 기반 LLM 답변**: 크롤링+조문 내용을 context로 LLM(OpenAI GPT) 답변 생성
- **참조된 법령 자동 추출**: 본문/조문 내 "법 제X조" 등 참조까지 모두 추출

### 2. 법령+조항 추출 (`law_article_extractor.py`)
- 정규표현식 기반 법령명+조문번호 패턴 매칭
- 다양한 법령 유형 지원 및 중복 제거
- 본문/조문 내 참조까지 추출 가능

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
# Tavily API (검색)
TAVILY_API_KEY=your_tavily_api_key_here
# 법제처 OpenAPI (조문 내용)
LAW_API_KEY=your_law_api_key_here
# OpenAI LLM (RAG 답변)
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. API 키 발급
- **Tavily API**: [Tavily AI](https://tavily.com/)에서 무료 API 키 발급
- **법제처 OpenAPI**: [국가법령정보센터](https://www.law.go.kr/)에서 OpenAPI 키 발급
- **OpenAI API**: [OpenAI](https://platform.openai.com/)에서 API 키 발급

## 사용법

### 1. 통합 검색 + LLM 답변
```python
from law_search_integrated import LawSearchIntegrated

searcher = LawSearchIntegrated()
results = await searcher.crawl_and_extract_laws(
    "건축법에서 경미한 사항의 변경이란?", 
    domains=["law.go.kr"], 
    num_results=3
)
print(searcher.format_results(results))
```

### 2. 법령명+조문번호 추출
```python
from law_article_extractor import extract_law_articles
text = "건축법 제12조에 따르면 건축허가를 받아야 한다."
articles = extract_law_articles(text)
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
python law_search_integrated.py
```

### 출력 예시
```
=== 통합 법령 검색 시스템 ===

사용자 질문: 건축법에서 경미한 사항의 변경이란?

# 검색 결과: '건축법에서 경미한 사항의 변경이란?'

## 📋 발견된 법령 (1개)

### 직접 언급된 법령
1. **건축법 시행령** 제12조

### 참조된 법령
1. **건축법** 제16조 (법령참조)
2. **건축법** 제14조 (법령참조)
3. **건축법** 제11조 (법령참조)

## 🤖 LLM 답변

건축법 시행령 제12조에 따르면, "대통령령으로 정하는 경미한 사항의 변경"이란 신축, 증축, 개축, 재축, 이전, 대수선 또는 용도변경에 해당하지 아니하는 변경을 의미합니다. ...
```

## 주요 특징

- **검색+크롤링+법령 추출+조문 내용+LLM 답변** 완전 자동화
- **참조 조항까지 자동 추출** (본문/조문 내 "법 제X조" 등)
- **크롤링 로그 억제**: Crawl4AI 진행 메시지 미출력
- **RAG 기반 LLM 답변**: 법령 근거를 인용하는 답변 생성

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

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 