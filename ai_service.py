from __future__ import annotations
import os, json, re
from datetime import datetime
from zoneinfo import ZoneInfo


def ai_status():
    return {
        "configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        "web_search": True,
    }


def _parse_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise ValueError("AI 응답에서 JSON을 찾지 못했습니다.")
        return json.loads(m.group(0))


def market_scan():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
    from openai import OpenAI
    # HTTP Authorization headers must be ASCII. Korean prompts are UTF-8 safe,
    # but an API key copied with a label/whitespace/non-ASCII character is not.
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    try:
        api_key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(
            "OPENAI_API_KEY 값에 한글/특수문자가 섞여 있습니다. Render Environment에는 OpenAI API 키 값만 다시 붙여넣어 주세요."
        ) from exc
    if not api_key.startswith("sk-"):
        raise RuntimeError("OPENAI_API_KEY 형식이 올바르지 않습니다. OpenAI API 키 값만 입력해 주세요.")
    client = OpenAI(api_key=api_key)
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    prompt = f"""
현재 시각은 한국시간 {now:%Y-%m-%d %H:%M}이다.
웹 검색을 반드시 사용해서 한국 주식시장(KOSPI/KOSDAQ)의 최근 주도 섹터와 주도주 후보를 조사하라.
목표는 투자 추천이 아니라 '시장 주도력 탐색'이다.

규칙:
1. 오늘 또는 가장 최근 거래일 자료를 우선한다.
2. 확인되지 않은 가격, 거래대금, 외국인/기관 순매수 숫자는 절대 만들어내지 않는다.
3. 거래대금/수급 숫자가 웹에서 신뢰성 있게 확인되지 않으면 null로 둔다.
4. 종목은 최대 12개, 섹터는 최대 8개.
5. 각 종목은 최근 뉴스/공시/산업 모멘텀과 왜 주도주 후보인지 1~2문장으로 설명한다.
6. 가능한 경우 종목코드 6자리를 넣는다.
7. source_urls에는 실제 조사에 사용한 URL만 넣는다.
8. 결과는 아래 JSON 하나만 출력한다. 마크다운 금지.

{{
 "as_of":"YYYY-MM-DD HH:MM KST",
 "market_summary":"...",
 "sectors":[{{"sector":"반도체","strength":0,"reason":"..."}}],
 "candidates":[{{
   "name":"종목명","ticker":"000000","sector":"...","ai_score":0,
   "reason":"...","catalyst":"...",
   "price":null,"change_pct":null,"turnover_krw":null,
   "foreign_net_krw":null,"institution_net_krw":null,
   "data_note":"숫자 확인 여부 설명"
 }}],
 "source_urls":["https://..."]
}}

ai_score는 0~100의 'AI 시장 주도력 신호'이며 투자수익 전망 점수가 아니다.
"""
    resp = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        tools=[{"type":"web_search", "search_context_size":"medium"}],
        tool_choice="required",
        input=prompt,
    )
    data = _parse_json(resp.output_text)
    data["source"] = "OpenAI web search"
    data["generated_at"] = now.isoformat()
    data["model"] = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    return data
