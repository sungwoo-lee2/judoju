# Leader Finder v13 KRX
기존 AI 시장탐색 기능을 유지하고 주식 숫자를 KRX 공식 인증 API로 조회합니다.

## 기존 Render 서비스 업데이트
압축 해제한 파일을 기존 GitHub 저장소에 교체하고 Commit합니다.
Render Environment에 KRX_API_KEY = 발급받은 실제 KRX 인증키를 설정합니다.
인증키 발급 외에 유가증권 일별매매정보(stk_bydd_trd), 코스닥 일별매매정보(ksq_bydd_trd) 이용승인이 필요합니다.
Manual Deploy → Deploy latest commit. 기존 서비스 삭제 또는 새 서비스 생성 불필요.
Build: pip install -r requirements.txt
Start: uvicorn app:app --host 0.0.0.0 --port $PORT
앱에서 데이터 새로고침. 데이터 연결 진단으로 인증 오류, 시간 초과, 빈 응답 확인.

## 제공 범위
종가, 등락률, 거래량, 거래대금, 시가총액, 기준일. 실시간 시세 아님.
한국시간 전일부터 조회하여 두 시장 자료가 모두 있는 최신 날짜 사용.
외국인/기관 수급, 20일 평균, 52주 고점은 이 API에서 제공되지 않아 계산하지 않음.
일별 후보점수 = 전체 응답 종목 거래대금 백분위 70% + 등락률 백분위 30%.
거래대금 상위 UNIVERSE_SIZE(기본 80) 종목 중 점수 상위 20개 표시.
초기주도/눌림목/섹터/성과 탭은 근거자료가 없어 비워두며 AI 기능은 별도 사용 가능.
조회 실패 시 마지막 성공 데이터를 유지하며 샘플 데이터로 대체하지 않음.
API 키는 서버 환경변수에만 저장. GitHub나 브라우저에 넣지 마세요.

## 검증
python3 -m unittest test_krx_api -v
인증 헤더/요청일, 403 오류, 숫자 변환, 수급 미생성, 스냅샷 저장 테스트 통과.
실제 사용자 인증키와 Render 배포 권한이 없어 실서비스 인증 조회는 검증하지 못함.
공식 안내: https://openapi.krx.co.kr/
