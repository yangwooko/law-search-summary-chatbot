# 📘 Plan: 법령 기반 질문 응답 챗봇 구현

## 🎯 목표

질문자가 입력한 질문에 대해 관련된 **법령 조문**들을 수집하고, **조문 간 참조 관계를 추적**하여 정확한 문맥을 구성한 뒤, **LLM이 그 문맥에 기반하여 답변**할 수 있는 시스템을 구현한다.

- 대상: 법률, 시행령, 시행규칙 등
- 상황: 질문자가 법률 용어나 키워드를 포함한 질문을 입력함
- 제한: LLM의 컨텍스트 길이가 제한되어 있음 → Chunking + 요약 + RAG 구조 필요

---

## 🧱 시스템 아키텍처

```plaintext
[질문]
   ↓
[관련 법령 검색 (구글 CSE)]
   ↓
[법령 API로 조문 수집]
   ↓
[조문 간 참조 관계 추적 (재귀)]
   ↓
[중요 조문 필터링 및 일부 요약]
   ↓
[Chunk 단위 RAG + 부분 추론]
   ↓
[LLM 통합 응답 생성]
````

---

## 🔄 조문 처리 전략

### 1. 조문 수집

* 사용처: 법제처 API
* 지원 예시: `건축법 제16조`, `건축법 시행령 제14조`

### 2. 조문 간 참조 추적

* 조문에 포함된 <a> 링크를 추적 
* depth 2\~3까지 추적
* 무한 순환 방지 로직 포함

### 3. LLM 컨텍스트 초과 대응

#### a. 유사도 기반 상위 N개만 선택

* LLM을 이용하여 질문과의 유사도를 판별하여 관련도 높은 조문 상위 선택

#### b. 조문을 이용한 부분 질의

* 조문 1개씩 또는 조문이 작은 경우 여러개를 묶어서 각각 질의
* 예: `["조문 A + B"] → LLM → 부분 응답`

#### c. 요약 후 통합

* 각 응답들을 다시 LLM에 넘겨서 하나의 답변으로 통합

---

## 🧠 프롬프트 구조 예시

```text
[질문]
건축 허가를 받은 후 경미한 변경을 하면 어떤 신고가 필요한가요?

[관련 법령 문맥]
- 건축법 제16조: 변경 시 신고 필요. 경미한 변경 예외.
- 시행령 제14조: 경미한 변경의 구체적 기준.
- 시행규칙 제7조: 신고 절차 및 문서 양식 설명.
...

[지시]
질문에 대해 위 법령 내용을 바탕으로 정확하고 간결하게 답하십시오.
```

---

## 🛠️ 필요 기술 스택

* Python 3.10+
* OpenAI API
* Requests / aiohttp (API 호출)
* Tiktoken (토큰 길이 측정)

---

## 확장 기능

* 출처 조문 링크 자동 포함
* 챗 UI 연결 (FastAPI + React)
* 시각화: 조문 간 참조 트리 구조 렌더링

---
