import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import os
import re
import streamlit.components.v1 as components

# --- 페이지 설정 ---
st.set_page_config(page_title="트립은 블로그 올인원 스튜디오", layout="wide", page_icon="✈️")

st.markdown("""
<style>
    .main-title { font-size: 26px; font-weight: bold; color: #1e1e1e; margin-bottom: 4px; }
    .sub-title { font-size: 14px; color: #666; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>✈️ 트립은 블로그 올인원 스튜디오</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>사진 다중 분석 & 트립은 스타일 2,000자~4,000자 모바일 최적화 블로그 글 완성</div>", unsafe_allow_html=True)

# --- 안전한 API 키 설정 (비밀 금고 우선 연동) ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif os.environ.get("GEMINI_API_KEY"):
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.sidebar.header("🔑 Gemini API 설정")
    api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password", help="Google AI Studio에서 발급받은 API 키를 넣어주세요.")
    if not api_key:
        st.info("👈 웹사이트 왼쪽 사이드바에 Gemini API Key를 입력해주세요!")
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

    generate_btn = st.button("🚀 원고 생성하기 (2,000자~4,000자)", type="primary", use_container_width=True)

with col2:
    st.subheader("📝 3. 완성된 원고 & 검수 리포트")
    output_container = st.empty()

    if generate_btn:
        if not post_title or not target_keyword or not main_details or not practical_info:
            st.warning("⚠️ 제목, 키워드, 주요 내용, 실용 정보는 필수 입력 사항입니다.")
        else:
            with st.spinner("사진들을 분석하고 2,000자~4,000자 규격 맞춤 원고를 작성하고 있습니다... (약 20~35초 소요)"):
                
                system_instruction = f"""
당신은 네이버 인기 여행 전문 블로거 '여행블로거 트립은'입니다.
전달받은 [사진들]을 분석하고, 아래 엄격한 고정 규칙을 100% 준수하여 생생하고 솔직한 블로그 글을 작성하세요.

[고정 규칙]
1. 분량 규칙 (절대 엄수 - 최우선 규칙):
   - 최종 본문 분량: **공백 포함 반드시 2,000자 이상, 4,000자 미만** (적정 목표: 2,500자~3,500자)
   - **절대로 4,000자를 넘기면 안 됩니다.** 불필요하게 말을 늘어놓거나 사족을 길게 쓰지 마세요.
   - 2,000자 미만으로 너무 짧아도 안 됩니다.
   - docx 파일 등 외부 파일 없이 순수 텍스트 본문으로 바로 작성합니다.

2. 마크다운 특수문자 및 따옴표 절대 사용 금지:
   - 별표 기호(** 또는 *) 절대 사용 금지! 굵은 글씨용 별표 쓰지 마세요.
   - 샵 기호(#, ##, ###) 절대 사용 금지!
   - 큰따옴표(") 절대 사용 금지!
   - 소제목은 마크다운 기호 없이 오직 [소제목 이름] 형태로만 표기하세요.
   - 네이버 블로그 스마트에디터에 바로 붙여넣을 수 있는 순수 텍스트만 출력하세요.

3. 모바일 가독성 줄바꿈 및 문장 규칙:
   - 글이 벽돌처럼 뭉쳐 있으면 안 됩니다.
   - 1~2문장이 끝날 때마다 반드시 '빈 줄(엔터 2번)'을 넣어 시각적인 여백을 확보하세요.
   - 스마트폰 화면에서 스크롤을 내리며 가볍게 읽을 수 있도록 리듬감 있게 호흡을 띄워 작성하세요.
   - 한 줄당 공백포함 최대 30자여야 합니다. 30자가 넘으면 안됩니다. 그 이상의 문장이라면 엔터를 써서 줄나눔을 하여 작성하세요. 

4. 사진 묶기 및 태그 규칙:
   - 사진 한 장마다 억지로 말을 늘이지 마세요.
   - 유사한 장면이나 연속된 사진은 2~3개씩 묶어서 배치하세요. (예: [사진 1, 2: 매장 외관 및 웨이팅 현장], [사진 3, 4: 산리오 굿즈 코너 모음])
   - 묶은 사진 단위로 간결하고 생생하게 설명하세요.
   - 사진 태그 위아래로도 빈 줄(엔터)을 넣어 깔끔하게 분리하세요.

5. 블로거 정체성 & 기본 설정:
   - 블로거 이름: 여행블로거 트립은
   - 모든 글은 "안녕하세요, 여행블로거 트립은이에요!" 로 시작합니다. (따옴표 없이 텍스트만 출력)
   - 1인칭 시점, 실제 경험한 사람처럼 생생하게 작성합니다.
   - 독자를 항상 "여러분" 으로 지칭합니다.

6. 제목 & 키워드 규칙:
   - 제목: {post_title} (제목 자체는 변경하지 않고 그대로 사용)
   - 제목에 포함된 단어는 게시글 본문에 전부 최소 1회씩 반드시 자연스럽게 등장해야 합니다.
   - 키워드 {target_keyword}는 본문 전체에서 반드시 최소 4회, 최대 6회 자연스럽게 분산 삽입하세요.

7. 문체 & 톤 규칙:
   - 친근하고 솔직한 구어체 (~더라구요, ~했어요, ~이었음!, ~인 것 같아요)
   - 줄임말과 구어적 표현 자연스럽게 사용 (당근, 냉큼, 완전, 진~~짜, 너~~무)
   - 감탄과 강조는 물결표(~), 느낌표(!), 말줄임표(..) 적극 활용
   - 이모지는 과하지 않게, 포인트로만 사용 (ㅠㅠ, ㅎㅎ, : ) 등 텍스트 이모티콘 혼용)
   - 장점 강조 시 물결표 늘이기 (진~짜, 완~~전, 너무너무)
   - 중간중간 혼잣말 느낌의 코멘트 필수 배치 (이게 진짜였음.., 아직도 잊혀지지 않음.., 존맛.., 진짜 좋았어용 ㅠ..)
   - 독자에게 직접 말 거는 문장 포함 (여러분도 꼭 드셔보세요!, 이거 진짜 강추..!)
   - 과장된 표현으로 유머 추가 (면 추가 안 하면 불법임 ㅠㅠ, 이럴 때마다 술 못먹는 제가 원망스러워져요 등)
   - 솔직한 단점이나 아쉬운 점도 가감 없이 언급하고 개인 에피소드 반영

8. 게시글 구조:
   - [도입부]: 안녕하세요, 여행블로거 트립은이에요! 시작, 배경/계기 및 공감 상황 (간결하게 2~3줄 작성 후 엔터)
   - [소제목: 제목 반복 or 핵심 정보]: 장소명/상품명 + 주소 또는 핵심 정보 블록
   - [접근성 & 기본 정보]: 가는 방법, 위치, 운영시간, 실용 정보
   - [메인 경험 섹션]: 2~4개 소제목으로 구분 (음식의 경우: 비주얼 묘사 -> 맛 묘사 -> 개인 감상 순서 / 수치 정보 포함)
   - [총평 or 마무리]: 전체 경험 한 줄 요약, 가성비 평가 (가격 대비 만족도), 재방문 의사/추천 대상, 권유형 마무리

9. 가격 & 정보 표기 방식:
   - 일본 관련 글일 경우 엔화 표기 후 괄호 안에 한화 환산 병기.
   - 가격 정보는 자연스러운 문장 안에 녹이기.
   - 표(table)가 필요한 경우 깔끔한 표 형식 사용.
   - 실용 팁은 별도 줄 또는 [실용 팁] 소제목으로 강조.
   - 없는 정보는 지어내지 말고 파악된 정보만 포함.

10. 작성 시 금지 사항:
   - **4,000자 초과 절대 금지** (장황하게 늘어놓지 말 것)
   - 2,000자 미달 금지
   - **, *, #, " 기호 사용 절대 금지
   - 긴 문단으로 뭉쳐 쓰는 행위 절대 금지 (1~2문장 단위 줄바꿈 엄수)
   - 지나치게 격식체 or 광고성 홍보 문체 금지
   - 소제목 남발 금지
   - 키워드 몰아넣기 금지
   - 제목 단어 누락 금지
"""

                prompt_user = f"""
[입력 정보]
- 제목: {post_title}
- 키워드: {target_keyword}
- 주요 내용/경험: {main_details}
- 실용 정보: {practical_info}
- 강조 포인트: {highlight_point}

본문을 작성할 때 다음 사항을 철저히 지켜주세요:
1. 분량: 반드시 '공백 포함 2,000자 이상 ~ 4,000자 미만'으로 작성하세요. 4,000자를 절대 넘기지 마세요!
2. 서식: 본문 어디에도 **, *, # 기호와 큰따옴표(")를 절대 쓰지 마세요. 소제목은 [소제목] 형태로만 쓰세요.
3. 모바일 줄바꿈: 문장을 짧게 끊고, 1~2문장마다 반드시 빈 줄(엔터 2번)을 넣어주세요.
4. 사진 태그: 2~3장씩 묶어서 [사진 1, 2: ...] 형태로 작성해주세요.
5. 키워드: '{target_keyword}'는 본문 전체에서 4회~6회만 들어가도록 자연스럽게 분산 삽입해주세요.
"""

                contents = []
                for img in processed_images:
                    contents.append(img)
                contents.append(prompt_user)

                try:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                            max_output_tokens=4500,
                        )
                    )
                    
                    final_text = response.text

                    # 4,000자 초과 시 강력한 압축 루프
                    if len(final_text) >= 4000:
                        trim_prompt = f"""
현재 글의 분량이 {len(final_text)}자로 4,000자를 초과했습니다!
규칙 위반이므로, 글의 톤앤매너, 짧은 문장(1~2문장마다 엔터 빈 줄), 키워드({target_keyword} 4~6회), 사진 묶음 태그는 유지하면서
중복되거나 늘어진 묘사를 깔끔하게 쳐내어 전체 글자 수를 '공백 포함 2,500자~3,300자 사이'로 확실히 줄여 다시 작성해주세요.
주의: 본문에 **, *, #, " 기호는 절대 쓰지 마세요. 4,000자 초과는 절대 금지입니다.

[현재 초안]
{final_text}
"""
                        trim_response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[trim_prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7,
                            )
                        )
                        final_text = trim_response.text

                    # 2,000자 미달 시 보강 루프
                    elif len(final_text) < 2000:
                        expand_prompt = f"""
현재 글의 분량이 {len(final_text)}자로 2,000자 미만입니다.
'공백 포함 2,000자 이상, 4,000자 미만' 기준을 충족하기 위해, 
기존 톤앤매너, 모바일 줄바꿈, 키워드 빈도(4~6회)를 지키며 감상과 실용 꿀팁을 보강해 2,300자~3,000자 내외로 다시 작성해주세요.
주의: 본문에 **, *, #, " 기호는 절대 쓰지 마세요.

[현재 초안]
{final_text}
"""
                        expand_response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[expand_prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7,
                            )
                        )
                        final_text = expand_response.text

                    # 🛠️ 1. 마크다운 특수기호 및 따옴표 2차 자동 박멸 필터링
                    final_text = final_text.replace("**", "").replace('"', "")
                    clean_lines = []
                    for line in final_text.split("\n"):
                        stripped = line.lstrip()
                        if stripped.startswith("#"):
                            line = stripped.lstrip("#").strip()
                        clean_lines.append(line)
                    final_text = "\n".join(clean_lines)

                    # 🛠️ 2. 파이썬 모바일 강제 엔터 분할기 (1~2문장마다 강제 빈 줄 삽입)
                    paragraphs = final_text.split("\n\n")
                    formatted_paragraphs = []
                    for para in paragraphs:
                        para = para.strip()
                        if not para:
                            continue
                        if para.startswith("[") and para.endswith("]"):
                            formatted_paragraphs.append(para)
                            continue
                        
                        sentences = re.split(r'(?<=[.!?~])\s+', para)
                        chunk = []
                        for s in sentences:
                            chunk.append(s.strip())
                            if len(chunk) >= 2:
                                formatted_paragraphs.append(" ".join(chunk))
                                chunk = []
                        if chunk:
                            formatted_paragraphs.append(" ".join(chunk))

                    final_text = "\n\n".join(formatted_paragraphs)

                    # 검증 로직
                    char_count = len(final_text)
                    kw_count = final_text.count(target_keyword)
                    
                    title_words = [w for w in post_title.split() if len(w) > 1]
                    missing_words = [w for w in title_words if w not in final_text]

                    with output_container.container():
                        st.success("원고 생성이 완료되었습니다! 🎉")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("공백 포함 글자 수", f"{char_count}자", delta="적정 범위 (2천~4천자)" if 2000 <= char_count < 4000 else f"범위 확인 ({char_count}자)")
                        m2.metric("키워드 출현 횟수", f"{kw_count}회", delta="정상 (4~6회)" if 4 <= kw_count <= 6 else "수정 권장")
                        m3.metric("제목 단어 누락", f"{len(missing_words)}개", delta="전체 포함 완료" if not missing_words else f"누락: {', '.join(missing_words)}")

                        # 📋 1. 원클릭 클립보드 복사 큰 버튼
                        escaped_text = final_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                        copy_html = f"""
                        <div style="margin: 12px 0;">
                            <button id="copyBtn" onclick="copyContent()" style="
                                width: 100%;
                                background: linear-gradient(135deg, #03C75A 0%, #00B14F 100%);
                                color: white;
                                border: none;
                                padding: 14px 20px;
                                border-radius: 8px;
                                font-size: 16px;
                                font-weight: bold;
                                cursor: pointer;
                                box-shadow: 0 4px 10px rgba(3, 199, 90, 0.25);
                                transition: all 0.2s ease;
                            ">📋 원고 전체 클립보드에 복사하기</button>
                        </div>
                        <script>
                        function copyContent() {{
                            const text = `{escaped_text}`;
                            navigator.clipboard.writeText(text).then(function() {{
                                const btn = document.getElementById("copyBtn");
                                btn.innerText = "✅ 복사 완료! 네이버 블로그에 바로 붙여넣기 하세요!";
                                btn.style.background = "#1e1e1e";
                                setTimeout(function() {{
                                    btn.innerText = "📋 원고 전체 클립보드에 복사하기";
                                    btn.style.background = "linear-gradient(135deg, #03C75A 0%, #00B14F 100%)";
                                }}, 2500);
                            }}).catch(function(err) {{
                                alert("복사 실패: " + err);
                            }});
                        }}
                        </script>
                        """
                        components.html(copy_html, height=65)

                        # 📋 2. 코드 블록 박스
                        st.caption("👇 박스 우측 상단 네모 아이콘(📋)을 눌러도 전체 복사됩니다:")
                        st.code(final_text, language="markdown")

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
