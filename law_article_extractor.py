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
