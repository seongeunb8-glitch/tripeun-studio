import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="트립은 블로그 올인원 스튜디오", layout="wide", page_icon="✈️")

st.markdown("""
<style>
    .main-title { font-size: 26px; font-weight: bold; color: #1e1e1e; margin-bottom: 4px; }
    .sub-title { font-size: 14px; color: #666; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>✈️ 트립은 블로그 올인원 스튜디오</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>사진 다중 분석 & 트립은 스타일 3,000자~5,000자 블로그 글 자동 완성</div>", unsafe_allow_html=True)

# --- 안전한 API 키 설정 (깃허브 유출 방지) ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif os.environ.get("GEMINI_API_KEY"):
    api_key = os.environ.get("GEMINI_API_KEY")

# 환경변수/Secrets가 없을 경우 웹 화면 사이드바에서 안전하게 직접 입력
if not api_key:
    st.sidebar.header("🔑 Gemini API 설정")
    api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password", help="Google AI Studio에서 발급받은 API 키를 넣어주세요.")
    if not api_key:
        st.info("👈 웹사이트 왼쪽 사이드바(화면 좌측 상단 화살표 > 클릭)에 Gemini API Key를 입력해주세요!")
        st.stop()

client = genai.Client(api_key=api_key)

# 2열 반응형 레이아웃
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📷 1. 여행 사진 여러 장 넣기 (자동 분석)")
    uploaded_files = st.file_uploader(
        "방문 순서대로 사진들을 선택해주세요 (외관, 내부, 음식 등)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    processed_images = []
    if uploaded_files:
        st.success(f"총 {len(uploaded_files)}장의 사진이 업로드되었습니다.")
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, file in enumerate(uploaded_files):
            img = Image.open(file)
            img.thumbnail((1024, 1024))
            processed_images.append(img)
            with cols[idx % 4]:
                st.image(img, caption=f"사진 {idx+1}", use_container_width=True)

    st.markdown("---")
    st.subheader("✍️ 2. 포스팅 정보 입력")
    
    post_title = st.text_input(
        "제목 *", 
        placeholder="예: 후쿠오카 가볼만한곳 하카타 버스터미널 일본 다이소 쇼핑 내돈내산"
    )
    target_keyword = st.text_input(
        "필수 키워드 (4~6회 분산 삽입) *", 
        placeholder="예: 후쿠오카 가볼만한곳"
    )
    main_details = st.text_area(
        "주요 내용 / 경험 *", 
        placeholder="예: 주말 오후 2시 방문, 외국인들 북적북적. 일본 다이소 산리오 상품 많았음. sns에서 유명한 제품들 재고 많음."
    )
    practical_info = st.text_area(
        "포함할 실용 정보 (가격, 주소 등) *", 
        placeholder="예: 일본 〒812-0012 Fukuoka, Hakata Ward, Hakataekichuogai, 2−1 博多バスターミナル 店５階, 가격표 없는 물품 세금제외 100엔, 매일 09:00-21:00, 주차 불가 근처 공영주차장 이용"
    )
    highlight_point = st.text_input(
        "특별히 강조하고 싶은 포인트", 
        placeholder="예: 하카타역 바로 앞에 있어 접근성이 정말 좋고, 후쿠오카 여행 중 쇼핑하러 와볼만한 곳"
    )

    generate_btn = st.button("🚀 사진 분석 & 트립은 맞춤 원고 생성", type="primary", use_container_width=True)

with col2:
    st.subheader("📝 3. 완성된 원고 & 검수 리포트")
    output_container = st.empty()

    if generate_btn:
        if not post_title or not target_keyword or not main_details or not practical_info:
            st.warning("⚠️ 제목, 키워드, 주요 내용, 실용 정보는 필수 입력 사항입니다.")
        else:
            with st.spinner("사진들을 순서대로 분석하며 트립은 스타일 원고를 작성하고 있습니다... (약 20~35초 소요)"):
                
                system_instruction = f"""
당신은 네이버 인기 여행 전문 블로거 '여행블로거 트립은'입니다.
전달받은 [사진들]을 순서대로 정밀 분석하고, 아래 엄격한 고정 규칙을 100% 준수하여 생생하고 솔직한 블로그 글을 작성하세요.

[고정 규칙]
1. 시작 문구: 반드시 "안녕하세요, 여행블로거 트립은이에요!" 로 시작합니다.
2. 독자 호칭: 항상 "여러분" 으로 지칭합니다.
3. 시점: 1인칭 시점, 실제 경험한 사람처럼 생생하게 작성합니다.
4. 문체 & 톤 규칙:
   - 친근하고 솔직한 구어체 ("~더라구요", "~했어요", "~이었음!", "~인 것 같아요")
   - 줄임말과 구어적 표현 자연스럽게 사용 ("당근", "냉큼", "완전", "진~~짜", "너~~무")
   - 감탄과 강조는 물결표(~), 느낌표(!), 말줄임표(..) 적극 활용
   - 이모지는 과하지 않게, 포인트로만 사용 (ㅠㅠ, ㅎㅎ, : ) 등 텍스트 이모티콘 혼용)
   - 장점 강조 시 물결표 늘이기 ("진~짜", "완~~전", "너무너무")
   - 문단은 2~5줄 단위로 짧게 끊고, 한 문단에 한 가지 이야기만 서술 (모바일 가독성 극대화)
   - 중간중간 혼잣말 느낌의 코멘트 필수 배치 ("존맛..", "진짜 좋았어용 ㅠ..")
   - 독자에게 직접 말 거는 문장 포함 ("여러분도 꼭 드셔보세요!", "이거 진짜 강추..!")
   - 가끔 과장된 표현으로 유머 추가 ("면 추가 안 하면 불법임 ㅠㅠ", "이럴 때마다 술 못먹는 제가 원망스러움 ㅋㅋㅠㅠ" 등)
   - 솔직한 단점이나 아쉬운 점도 가감 없이 언급하고 개인 에피소드 반영

5. 사진 매칭 (필수):
   - 업로드된 사진들을 순서대로 분석하여 글 문맥에 맞게 [사진 1: 사진 설명], [사진 2: 사진 설명] 태그를 본문 사이에 삽입하세요.
   - 각 사진의 시각적 디테일(비주얼, 색감, 조명 등)을 실제 눈으로 본 것처럼 맛깔나게 묘사하세요.

6. 제목 & 키워드 규칙:
   - 제목: "{post_title}" (제목 자체는 변경하지 않고 그대로 사용)
   - 제목에 포함된 단어는 게시글 본문에 전부 최소 1회씩 반드시 자연스럽게 등장해야 합니다.
   - 키워드 "{target_keyword}"는 본문 전체에서 최소 4회, 최대 6회 자연스럽게 분산 삽입하세요.

7. 게시글 구조:
   - [도입부]: "안녕하세요, 여행블로거 트립은이에요!"로 시작, 개인적 배경/계기 및 공감 상황 (간결하게 2~3줄)
   - [소제목: 제목 반복 or 핵심 정보]: 장소명/상품명 + 주소 또는 핵심 정보 블록
   - [접근성 & 기본 정보]: 가는 방법, 위치, 운영시간, 실용 정보
   - [메인 경험 섹션]: 2~4개 굵은 소제목으로 구분 (음식의 경우: 비주얼 묘사 -> 맛 묘사 -> 개인 감상 순서 / 수치 정보 포함)
   - [총평 or 마무리]: 전체 경험 한 줄 요약, 가성비 평가, 재방문 의사/추천 대상, "여러분들도 ~해보시는 건 어떨까요?" 식의 권유

8. 가격 및 분량 규격:
   - 일본 관련 글일 경우 엔화 표기 후 괄호 안에 한화 환산 병기.
   - docx 등 외부 파일로 생성하지 말고 순수 텍스트 본문으로 바로 작성.
   - 최종 본문 분량: **공백 포함 3,000자 이상 ~ 5,000자 미만** 엄수.

9. 금지 사항:
   - 지나치게 격식체 or 딱딱한 문어체 금지
   - "본 포스팅은..." 식의 블로그 광고 문체 금지
   - 소제목 남발 금지
   - 사실 확인 안 된 허위 정보 생성 금지
   - 키워드 연속 몰아넣기 금지
   - 제목 단어 누락 금지
"""

                prompt_user = f"""
[입력 정보]
- 제목: {post_title}
- 키워드: {target_keyword}
- 주요 내용/경험: {main_details}
- 실용 정보: {practical_info}
- 강조 포인트: {highlight_point}

업로드된 사진들의 시각 정보와 위 내용을 결합하여 본문을 작성해주세요.
분량은 반드시 공백 포함 3,000자 이상, 5,000자 미만이 되도록 각 코스별 묘사와 감상을 상세하게 풀어주세요.
"""

                contents = []
                for img in processed_images:
                    contents.append(img)
                contents.append(prompt_user)

                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                        )
                    )
                    
                    final_text = response.text

                    # 3,000자 미달 시 자동 분량 확장 루프
                    if len(final_text) < 2800:
                        expand_prompt = f"""
방금 작성한 글의 분량이 {len(final_text)}자로 3,000자 미만입니다. 
'공백 포함 3,000자 이상 5,000자 미만' 조건을 완벽히 충족하기 위해, 
기존 글의 톤앤매너, 사진 위치 태그([사진 1] 등), 키워드 빈도(4~6회 유지)를 지키면서 현장 분위기 묘사와 감상, 실용 꿀팁을 대폭 추가해 3,000자 이상으로 자연스럽게 늘려 다시 작성해주세요.

[현재 초안]
{final_text}
"""
                        expand_response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[expand_prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7,
                            )
                        )
                        final_text = expand_response.text

                    # 검증 로직
                    char_count = len(final_text)
                    kw_count = final_text.count(target_keyword)
                    
                    title_words = [w for w in post_title.split() if len(w) > 1]
                    missing_words = [w for w in title_words if w not in final_text]

                    with output_container.container():
                        st.success("원고 생성이 완료되었습니다! 🎉")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("공백 포함 글자 수", f"{char_count}자", delta="적정 범위 (3천~5천자)" if 3000 <= char_count < 5000 else f"범위 확인 ({char_count}자)")
                        m2.metric("키워드 출현 횟수", f"{kw_count}회", delta="정상 (4~6회)" if 4 <= kw_count <= 6 else "수정 권장")
                        m3.metric("제목 단어 누락", f"{len(missing_words)}개", delta="전체 포함 완료" if not missing_words else f"누락: {', '.join(missing_words)}")

                        st.text_area("스마트에디터용 원고 본문", value=final_text, height=550)

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
