import re
from typing import List, Dict


def extract_law_articles(text: str) -> List[Dict[str, str]]:
    """
    텍스트에서 법령+조항 번호 쌍을 찾아냅니다.
    Args:
        text: 분석할 텍스트
    Returns:
        찾아진 법령+조항 정보 리스트
    """
    if not text:
        return []

    patterns = [
        r'(?:^|[\s"\'\(\[|])([가-힣\s]+법률\s*시행규칙)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r'(?:^|[\s"\'\(\[|])([가-힣\s]+법률\s*시행령)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r'(?:^|[\s"\'\(\[|])([가-힣\s]+법\s*시행규칙)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r'(?:^|[\s"\'\(\[|])([가-힣\s]+법\s*시행령)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r'(?:^|[\s"\'\(\[|])([가-힣\s]+법)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r'(?:^|[\s"\'\(\[|])([가-힣]+조례)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r'(?:^|[\s"\'\(\[|])([가-힣]+규칙)\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조',
        r"부칙\s*(?:\[[^\]]*\]\s*)*제\s*(\d+)\s*조",
        r"별표\s*(?:\[[^\]]*\]\s*)*(\d+)",
        r"별지\s*(?:\[[^\]]*\]\s*)*(\d+)",
    ]

    found_articles = []
    used_ranges = []
    remaining_text = text

    while remaining_text:
        best_match = None
        best_pattern_index = -1

        # 모든 패턴에서 첫 번째 매칭을 찾아서 가장 앞에 있는 것을 선택
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, remaining_text, re.IGNORECASE)
            if match:
                if best_match is None or match.start() < best_match.start():
                    best_match = match
                    best_pattern_index = i

        if best_match is None:
            break

        pattern = patterns[best_pattern_index]
        match = best_match
        start, end = match.start(), match.end()

        # 이미 추출된 범위와 겹치면 무시
        if any(not (end <= r[0] or start >= r[1]) for r in used_ranges):
            remaining_text = remaining_text[end:]
            continue

        # 패턴별 그룹 조합
        if pattern in patterns[:5]:
            law_name = match.group(1).strip()
            # '조문정보' 등 불필요한 앞 단어 사전 제거
            law_name = re.sub(r"^(조문정보|연계정보|\d+\.|\s+)+", "", law_name)
            # 맨 앞에 한글이 아닌 부분 제거
            law_name = re.sub(r"^[^가-힣]+", "", law_name)
            # 모든 법령명 매치 찾기 (end()가 가장 큰 매치)
            all_matches = list(
                re.finditer(
                    r"([가-힣]{2,}\s*)+(법률\s*시행규칙|법률\s*시행령|법\s*시행규칙|법\s*시행령|법)",
                    law_name,
                )
            )
            if all_matches:
                last_match = max(all_matches, key=lambda m: m.end())
                law_name = law_name[: last_match.end()].strip()
                # 한글 2자 이상으로 시작하는 부분만 남기기
                m2 = re.search(r"[가-힣]{2,}.*", law_name)
                if m2:
                    law_name = m2.group(0).strip()
            article_num = match.group(2)
        elif pattern.startswith("부칙"):
            law_name = "부칙"
            article_num = match.group(1)
        elif pattern.startswith("별표"):
            law_name = "별표"
            article_num = match.group(1)
        elif pattern.startswith("별지"):
            law_name = "별지"
            article_num = match.group(1)
        else:
            law_name = match.group(1).strip() if match.group(1) else ""
            article_num = match.group(2)
            # 이하 후처리 동일
            cleaned = re.sub(r"\[[^\]]*\]", "", match.group(0))
            m = re.search(r"(.+?)제\s*\d+\s*조", cleaned)
            if m:
                temp_law_name = m.group(1).strip()
                law_match = re.search(
                    r"([가-힣\s]*(?:법률|법)\s*(?:시행규칙|시행령))$", temp_law_name
                )
                if law_match:
                    law_name = law_match.group(1).strip()
                else:
                    law_match2 = re.search(r"([가-힣\s]*(?:법|법률))$", temp_law_name)
                    if law_match2:
                        law_name = law_match2.group(1).strip()
                    else:
                        law_name = temp_law_name
            else:
                law_name = re.sub(r"^[^가-힣]+|[^가-힣\s]+$", "", law_name).strip()

        article_key = f"{law_name}_{article_num}"
        if not any(article["key"] == article_key for article in found_articles):
            found_articles.append(
                {
                    "law_name": law_name,
                    "article_num": article_num,
                    "key": article_key,
                    "full_text": match.group(0),
                    "start_pos": start,
                    "end_pos": end,
                }
            )
            used_ranges.append((start, end))

        # 처리한 부분 이후부터 다시 검색
        remaining_text = remaining_text[end:]

    found_articles.sort(key=lambda x: x["start_pos"])
    return found_articles


def extract_referenced_articles(
    text: str, current_law_name: str
) -> List[Dict[str, str]]:
    """
    텍스트에서 참조하는 조항들을 추출합니다.
    현재 법령명을 기준으로 "법 제X조" 같은 참조를 해석합니다.

    Args:
        text: 분석할 텍스트
        current_law_name: 현재 법령명 (예: "건축법 시행령")
    Returns:
        참조된 조항 정보 리스트
    """
    if not text or not current_law_name:
        return []

    # 현재 법령명에서 기본 법령명 추출 (예: "건축법 시행령" -> "건축법")
    base_law_name = current_law_name
    if "시행령" in current_law_name:
        base_law_name = current_law_name.replace(" 시행령", "")
    elif "시행규칙" in current_law_name:
        base_law_name = current_law_name.replace(" 시행규칙", "")

    referenced_articles = []

    # 참조 패턴들 (문맥을 고려한 패턴)
    reference_patterns = [
        # "법 제X조제Y항제Z호" 패턴 (가장 명확한 참조)
        r"법\s*제\s*(\d+)\s*조(?:\s*제\s*(\d+)\s*항)?(?:\s*제\s*(\d+)\s*호)?",
        # "법 제X조제Y항" 패턴
        r"법\s*제\s*(\d+)\s*조(?:\s*제\s*(\d+)\s*항)?",
        # "법 제X조" 패턴
        r"법\s*제\s*(\d+)\s*조",
    ]

    for pattern in reference_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            article_num = match.group(1)
            paragraph_num = (
                match.group(2) if len(match.groups()) > 1 and match.group(2) else None
            )
            sub_paragraph_num = (
                match.group(3) if len(match.groups()) > 2 and match.group(3) else None
            )

            # 이미 추출된 조항과 중복 확인
            article_key = f"{base_law_name}_{article_num}"
            if not any(
                article["key"] == article_key for article in referenced_articles
            ):
                referenced_articles.append(
                    {
                        "law_name": base_law_name,
                        "article_num": article_num,
                        "paragraph_num": paragraph_num,
                        "sub_paragraph_num": sub_paragraph_num,
                        "key": article_key,
                        "full_text": match.group(0),
                        "reference_type": "법령참조",
                        "start_pos": match.start(),
                        "end_pos": match.end(),
                    }
                )

    # 중복 제거 및 정렬
    unique_articles = []
    seen_keys = set()
    for article in referenced_articles:
        if article["key"] not in seen_keys:
            unique_articles.append(article)
            seen_keys.add(article["key"])

    unique_articles.sort(key=lambda x: x["start_pos"])
    return unique_articles


def extract_all_articles_with_references(
    text: str, current_law_name: str | None = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    텍스트에서 직접 언급된 법령 조항과 참조 조항을 모두 추출합니다.

    Args:
        text: 분석할 텍스트
        current_law_name: 현재 법령명 (참조 해석용)
    Returns:
        직접 언급된 조항과 참조 조항을 포함한 딕셔너리
    """
    # 직접 언급된 법령 조항 추출
    direct_articles = extract_law_articles(text)

    # 참조 조항 추출 (현재 법령명이 있는 경우)
    referenced_articles = []
    if current_law_name:
        referenced_articles = extract_referenced_articles(text, current_law_name)

    return {
        "direct_articles": direct_articles,
        "referenced_articles": referenced_articles,
        "all_articles": direct_articles + referenced_articles,
    }
