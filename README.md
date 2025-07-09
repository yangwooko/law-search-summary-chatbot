# 법령 검색 요약 챗봇

구글 Custom Search Engine(CSE)을 활용하여 법령 관련 정보를 검색하고, 텍스트에서 법령+조항 번호를 자동으로 추출하는 Python 프로젝트입니다.

## 주요 기능

### 1. 구글 CSE 검색 (`google_cse_search.py`)
- 구글 Custom Search Engine API를 통한 웹 검색
- 검색 결과에서 HTML 원문 텍스트 추출
- 법령+조항 자동 추출 및 요약
- **Fallback 기능**: CSE 사용 불가 시 일반 구글 검색으로 대체 (제한적)

### 2. 법령+조항 추출 (`law_article_extractor.py`)
- 정규표현식 기반 법령+조항 패턴 매칭
- 다양한 법령 유형 지원:
  - 법률 (예: 건축법)
  - 법률 시행령 (예: 건축법 시행령)
  - 법률 시행규칙 (예: 건축법 시행규칙)
  - 조례, 규칙
  - 부칙, 별표, 별지
- 중복 제거 및 후처리 로직

## 설치 및 설정

### 1. 의존성 설치
```bash
uv sync
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
```

## 사용법

### 기본 검색
```python
from google_cse_search import GoogleCSESearch

searcher = GoogleCSESearch()
results = searcher.search("건축법 제16조", 5)
```

### 법령+조항 추출
```python
from law_article_extractor import extract_law_articles

text = "건축법 제12조에 따르면 건축허가를 받아야 한다."
articles = extract_law_articles(text)
# 결과: [{'law_name': '건축법', 'article_num': '12', ...}]
```

### 통합 검색 및 추출
```python
# 검색과 법령+조항 추출을 동시에 수행
results = searcher.search_and_extract_law_articles("건축법 경미한 변경", 3)

# 고유한 법령+조항만 추출
unique_articles = searcher.get_unique_law_articles(results)

# 요약 정보 생성
summary = searcher.search_law_articles_summary("건축법 경미한 변경", 3)
```

## 테스트

### 법령+조항 추출 패턴 테스트
```bash
python -m pytest test_improved_pattern.py -v
```

### 구글 CSE 검색 테스트
```bash
python -m pytest test_google_cse.py -v
```

## 지원하는 법령 패턴

1. **기본 법률**: `건축법 제12조`
2. **시행령**: `건축법 시행령 제14조`
3. **시행규칙**: `건축법 시행규칙 제7조`
4. **조례/규칙**: `서울특별시조례 제123조`
5. **부칙/별표/별지**: `부칙 제1조`, `별표 1`, `별지 2`
6. **대괄호 부가정보**: `건축법[시행 2024.1.1] 제16조`

## 개발 과정

### 주요 개선사항
1. **정규표현식 패턴 최적화**: 다양한 법령 유형에 대한 정확한 매칭
2. **중복 제거 로직**: 동일한 법령+조항의 중복 추출 방지
3. **후처리 개선**: 불필요한 앞 단어 제거 및 법령명 정규화
4. **첫 번째 매칭 우선**: 텍스트에서 첫 번째로 발견되는 패턴 우선 처리
5. **Fallback 기능**: CSE 사용 불가 시 일반 구글 검색으로 대체

### 제한사항
- **일반 구글 검색 Fallback**: 구글의 봇 차단 정책으로 인해 안정성이 제한적
- **CSE 권장**: 안정적인 서비스를 위해서는 구글 CSE API 사용 권장

### 해결된 문제들
- 긴 법령명 처리 (예: "국토의 계획 및 이용에 관한 법률 시행규칙")
- 대괄호 부가정보 처리
- 줄바꿈 포함 텍스트 처리
- 불필요한 앞 단어 제거 (예: "조문정보", "변경 등")

## 프로젝트 구조

```
law-search-summary-chatbot/
├── google_cse_search.py      # 구글 CSE 검색 및 텍스트 추출
├── law_article_extractor.py  # 법령+조항 추출 로직
├── test_improved_pattern.py  # 법령 추출 패턴 테스트
├── test_google_cse.py        # 구글 CSE 검색 테스트
├── pyproject.toml           # 프로젝트 설정
├── uv.lock                  # 의존성 잠금 파일
└── env.example              # 환경 변수 예제
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 