import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageOps
import io
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
st.markdown("<div class='sub-title'>DSLR 대용량 40장 실시간 자동 리사이징 & 모바일 호흡 줄바꿈 완벽 적용 (2,000~4,000자)</div>", unsafe_allow_html=True)

# --- 안전한 API 키 설정 ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif os.environ.get("GEMINI_API_KEY"):
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.sidebar.header("🔑 Gemini API 설정")
    api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")
    if not api_key:
        st.info("👈 웹사이트 왼쪽 사이드바에 Gemini API Key를 입력해주세요!")
        st.stop()

client = genai.Client(api_key=api_key)

# --- 📷 DSLR 고화질 대용량 사진 실시간 자동 리사이징 & 압축 함수 ---
def resize_dslr_image(uploaded_file):
    img = Image.open(uploaded_file)
    # DSLR EXIF 회전 정보 유지 (세로 사진이 눕는 현상 방지)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    # 가로세로 최대 1024px로 실시간 리사이징 (9MB -> 약 150KB로 초고속 경량화)
    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    buf.seek(0)
    return Image.open(buf)

# --- 📱 모바일 호흡 줄바꿈 보정 함수 (문장 중간중간 엔터 강제 보장) ---
def format_mobile_lines(text, post_title):
    blocks = re.split(r'\n\s*\n', text.strip())
    final_blocks = []

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        new_lines = []
        for line in lines:
            if line == post_title or (line.startswith("[") and line.endswith("]")):
                new_lines.append(line)
                continue
            
            # 한 줄이 이미 22자 이하로 짧게 끊어져 있으면 그대로 유지
            if len(line) <= 22:
                new_lines.append(line)
            else:
                # 한 줄이 길면 어절 단위로 읽으면서 14~20자 호흡마다 중간 엔터(\n) 삽입
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if not current_line:
                        current_line = word
                    else:
                        temp = current_line + " " + word
                        if len(temp) > 19 or (len(current_line) >= 10 and current_line.endswith(('고', '서', '며', '는데', '지만', '니까', '더니', '해서', '있고', '많고', ',', '요!', '요~', '음..', '어요.'))):
                            new_lines.append(current_line)
                            current_line = word
                        else:
                            current_line = temp
                if current_line:
                    new_lines.append(current_line)

        # 한 문단이 5줄을 넘어가면 3~4줄 단위로 빈 줄(문단) 분리
        if len(new_lines) > 5 and not (new_lines[0].startswith("[") and new_lines[0].endswith("]")):
            for i in range(0, len(new_lines), 4):
                chunk = new_lines[i:i+4]
                final_blocks.append("\n".join(chunk))
        else:
            final_blocks.append("\n".join(new_lines))

    return "\n\n".join(final_blocks)


col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📷 1. 여행 사진 업로드 (DSLR 40장 실시간 리사이징)")
    uploaded_files = st.file_uploader(
        "방문 순서대로 DSLR 원본 사진들을 선택해주세요 (장당 9MB 이상 대용량 자동 압축 지원)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    processed_images = []
    if uploaded_files:
        with st.spinner(f"총 {len(uploaded_files)}장의 DSLR 고화질 사진을 실시간 리사이징하고 있습니다..."):
            cols = st.columns(min(len(uploaded_files), 6))
            for idx, file in enumerate(uploaded_files):
                resized_img = resize_dslr_image(file)
                processed_images.append(resized_img)
                with cols[idx % 6]:
                    st.image(resized_img, caption=f"사진 {idx+1}", use_container_width=True)
        st.success(f"✅ 총 {len(processed_images)}장 실시간 자동 리사이징 완료! (초고속 전송 준비 완료)")

    st.markdown("---")
    st.subheader("✍️ 2. 작성 전 입력 체크리스트")
    
    post_title = st.text_input("제목 *", placeholder="예: 후쿠오카 가볼만한곳 하카타 버스터미널 일본 다이소 쇼핑 내돈내산")
    target_keyword = st.text_input("키워드 (4~6회 자연스럽게 삽입) *", placeholder="예: 후쿠오카 가볼만한곳")
    main_details = st.text_area("주요 내용/경험 *", placeholder="예: 주말 오후 2시 방문, 외국인들 북적북적. 일본 다이소 산리오 상품 많았음. sns에서 유명한 제품들 재고 많음.")
    practical_info = st.text_area("포함할 실용 정보 (가격, 주소 등) *", placeholder="예: 일본 〒812-0012 Fukuoka, Hakata Ward, Hakataekichuogai, 2−1 博多バスターミナル 店５階, 가격표 없는 물품 세금제외 100엔, 매일 09:00-21:00")
    highlight_point = st.text_input("특별히 강조하고 싶은 포인트", placeholder="예: 하카타역 바로 앞에 있어 접근성이 정말 좋고, 후쿠오카 여행 중 쇼핑하러 와볼만한 곳")

    generate_btn = st.button("🚀 원고 생성하기", type="primary", use_container_width=True)

with col2:
    st.subheader("📝 3. 완성된 원고 & 검수 리포트")
    output_container = st.empty()

    if generate_btn:
        if not post_title or not target_keyword or not main_details or not practical_info:
            st.warning("⚠️ 제목, 키워드, 주요 내용/경험, 포함할 실용 정보는 필수 입력 사항입니다.")
        else:
            with st.spinner(f"리사이징된 사진 {len(processed_images)}장을 분석하고 모바일 줄바꿈을 적용해 작성하고 있습니다... (약 25~35초 소요)"):
                
                system_instruction = f"""
# 📝 트립은 블로그 게시글 생성 프롬프트

---

## 🔒 고정 규칙 (반드시 준수)

**제목 규칙:**
- 만들어진 게시글 맨 위(최상단 첫 줄)에 내가 만든 제목({post_title})을 그대로 한 줄 삽입하고 빈 줄을 넣을 것
- 제목에 포함된 단어는 게시글 본문에 전부 최소 1회씩 자연스럽게 등장해야 함
- 제목 자체는 변경하지 않고 그대로 사용

**키워드 규칙:**
- 지정된 키워드({target_keyword})는 게시글 전체에서 최소 4회, 최대 6회 자연스럽게 삽입
- 억지스럽게 끼워넣지 않고, 문맥상 자연스러운 위치에 배치

**분량 및 출력 형식 규칙:**
- 게시글은 공백 포함 2,000자 이상 ~ 4,000자 미만으로 작성 (4,000자 초과 절대 금지)
- docx 파일 등 외부 파일로 생성하지 말고 본문에 바로 작성
- 네이버 스마트에디터 복사를 위해 본문에 마크다운 특수기호(**, *, #, ")는 절대 사용하지 말 것 (소제목은 [소제목] 형태로만 표기)

**📷 DSLR 고화질 대용량 사진 30~40장 실시간 리사이징 & 묶음 분석 규칙:**
- 업로드 즉시 실시간 자동 리사이징되어 전달된 다량의 사진들을 방문 순서대로 면밀히 분석할 것
- 사진 한 장마다 억지로 말을 늘이지 말고, 유사한 장면이나 연속된 사진은 2~3장씩 묶어서 [사진 1, 2, 3: 사진 설명] 형태로 본문 흐름에 맞게 배치할 것
- 사진 속 외관, 내부 분위기, 음식 비주얼, 메뉴판, 소품 등을 파악해 그 사진에 딱 어울리는 생생한 문장으로 묘사할 것
- 사진 태그 위아래로는 반드시 빈 줄(엔터 2번)을 넣어 본문과 분리할 것

---

## 👤 블로거 정체성 & 기본 설정

- 블로거 이름: 여행블로거 트립은
- 상단 제목 바로 다음 줄부터 모든 글은 안녕하세요, 여행블로거 트립은이에요! 로 시작 (따옴표는 출력하지 않음)
- 1인칭 시점, 실제 경험한 사람처럼 작성
- 독자를 여러분 으로 지칭

---

## ✍️ 문체 & 톤 규칙

**말투:**
- 친근하고 솔직한 구어체 (~더라구요, ~했어요, ~이었음!, ~인 것 같아요, ~했슴!, ~있었슴!, ~좋았슴ㅠㅠ, 대박이었어유.. )
- 줄임말과 구어적 표현 자연스럽게 사용 (당근, 냉큼, 완전, 진~~짜, 너~~무, 겁나, 레전드)
- 감탄과 강조는 물결표(~), 느낌표(!), 말줄임표(..) 적극 활용
- 이모지는 과하지 않게, 포인트로만 사용 (ㅠㅠ, ㅎㅎ, : ) 등 텍스트 이모티콘도 혼용)
- 장점 강조할 때 물결표로 늘이기: 진~짜, 완~~전, 너무너무, 레전드, 킹왕짱, 개쩔었어요 

**📱 문단 구성 & 모바일 호흡 줄바꿈 (★핵심 필수★):**
- 문장이 길어지면 절대 안 됨!
  이렇게 하는 것처럼
  한 문장 안에서도 중간중간 엔터를 쳐서
  모바일 가독성을 높일 것 (한 줄당 3~5어절, 약 15~20자 내외로 짧게 끊어 엔터 치기)
- 이렇게 짧게 줄바꿈된 2~5줄이 모이면 빈 줄(엔터 2번)을 넣어 한 문단을 끝낼 것
- 한 문단에 한 가지 이야기만
- 중간중간 혼잣말 느낌의 코멘트 삽입 (이게 진짜였음.., 아직도 잊혀지지 않음.., 존맛.., 진짜 좋았어용 ㅠ..)
- 독자에게 직접 말 거는 문장 포함 (여러분도 꼭 드셔보세요!, 이거 진짜 강추..!)

**유머 & 개성:**
- 가끔 과장된 표현으로 재미 추가 (면 추가 안 하면 불법임 ㅠㅠ, 이럴 때마다 술 못먹는 제가 원망스러워져요)
- 솔직한 단점이나 아쉬운 점도 가감없이 언급
- 개인적인 에피소드와 감정을 섞어 생동감 부여

---

## 🏗️ 게시글 구조

[맨 위 제목 삽입]
- {post_title}

[도입부]
- 안녕하세요, 여행블로거 트립은이에요! 로 시작
- 이번 주제를 소개하게 된 개인적인 배경/계기
- 독자의 공감을 끌어내는 상황 설명
- 자연스럽게 본론으로 연결
- 모바일 호흡 줄바꿈을 적용하여 간결하게 작성

[소제목: 제목 반복 or 핵심 정보]
- 장소명/상품명 + 주소 또는 핵심 정보 블록 ([소제목] 형태 사용)

[접근성 & 기본 정보] (장소 관련 글일 경우)
- 가는 방법, 위치, 주변 환경
- 예약 여부, 운영 방식 등 실용 정보

[메인 경험 섹션] (2~4개 소제목으로 구분)
- 소제목은 마크다운 기호 없이 [소제목] 형태로만 처리
- 실시간 리사이징된 사진들을 분석하여 2~3장씩 묶은 [사진 1, 2: 설명] 태그와 함께 생생하게 서술
- 각 섹션마다 실제 경험 + 솔직한 감상
- 음식이라면: 비주얼 묘사 → 맛 묘사 → 개인 감상 순서
- 수치 정보(가격, 시간, 거리 등) 자연스럽게 포함

[총평 or 마무리]
- 전체 경험 한 줄 요약
- 가성비 평가 (가격 대비 만족도)
- 재방문 의사 or 추천 대상 언급
- 여러분들도 ~해보시는 건 어떨까요? 식의 마무리 권유

---

## 💰 가격 & 정보 표기 방식

- 일본 관련: 엔화(엔) 표기 후 괄호 안에 한화 환산 병기
- 가격 정보는 자연스러운 문장 안에 녹이기
- 표(table)가 필요한 경우 깔끔한 표 형식 사용
- 실용 팁은 별도 줄 또는 [실용 팁] 소제목으로 강조

---

## 🔍 정보 수집 & 활용 방식

게시글 작성 전 아래 정보를 최신 기준으로 반영:
주의: 없는 정보를 지어내지 말고, 정확하게 파악된 정보만 포함할 것.

1. 장소/상품 기본 정보: 주소, 운영시간, 가격, 예약 방법
2. 최신 리뷰 및 평판: 최근 방문자 후기 트렌드
3. 주변 정보: 인근 명소, 교통편, 함께 가기 좋은 코스
4. 시즌 정보: 현재 시기에 맞는 특이사항 (축제, 혼잡도 등)
5. 실용 팁: 한국인 여행자 관점에서 유용한 정보

---

## 🚫 작성 시 금지 사항

- 한 줄에 문장을 길게 쭉 이어 쓰는 행위 절대 금지 (무조건 중간중간 엔터 쳐서 짧게 내려 쓸 것)
- 마크다운 특수기호(**, *, #, ") 절대 사용 금지
- 공백 포함 4,000자 초과 절대 금지 및 2,000자 미달 금지
- 지나치게 격식체 or 딱딱한 문어체 사용 금지
- 본 포스팅은... 식의 블로그 광고 문체 금지
- 소제목이 너무 많아 구조가 복잡해지는 것 금지
- 사실 확인 안 된 정보를 단정적으로 서술 금지
- 키워드를 연속으로 몰아넣는 것 금지 (자연스럽게 분산)
- 제목 단어 중 누락되는 것 금지 (체크리스트로 확인 후 작성)
"""

                prompt_user = f"""
## ✅ 작성 전 입력 체크리스트

제목: {post_title}
키워드: {target_keyword}
주요 내용/경험: {main_details}
포함할 실용 정보 (가격, 주소 등): {practical_info}
특별히 강조하고 싶은 포인트: {highlight_point}

위 체크리스트와 실시간 리사이징된 사진들을 바탕으로 블로그 본문을 작성해주세요!
★반드시 지켜야 할 핵심 사항★:
1. 문장이 길어지면 안 된다는 건
   이렇게 하는 것처럼
   중간중간 엔터를 쳐서
   모바일 가독성을 높이라는 뜻입니다! 한 줄에 15~20자 내외만 들어가게 중간중간 엔터를 치세요!
2. 맨 첫 줄에는 제목({post_title})을 그대로 적고 빈 줄을 넣으세요.
3. 본문에 **, *, #, " 기호는 절대 쓰지 마세요.
4. 업로드된 사진들을 순서대로 분석해 2~3장씩 묶어서 [사진 1, 2: 설명] 형태로 넣어주세요.
5. 전체 분량은 공백 포함 2,000자 이상 ~ 4,000자 미만으로 작성해주세요.
6. 키워드 '{target_keyword}'는 전체에서 4~6회만 자연스럽게 분산 삽입해주세요.
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
                            temperature=0.75,
                            max_output_tokens=4500,
                        )
                    )
                    
                    final_text = response.text

                    # 1. 마크다운 기호 및 따옴표 제거
                    final_text = final_text.replace("**", "").replace('"', "")
                    clean_lines = []
                    for line in final_text.split("\n"):
                        stripped = line.lstrip()
                        if stripped.startswith("#"):
                            line = stripped.lstrip("#").strip()
                        clean_lines.append(line)
                    final_text = "\n".join(clean_lines).strip()

                    # 2. 최상단 제목 강제 보장
                    if not final_text.startswith(post_title):
                        final_text = f"{post_title}\n\n{final_text}"

                    # 3. 모바일 호흡 줄바꿈 보정
                    final_text = format_mobile_lines(final_text, post_title)

                    char_count = len(final_text)
                    kw_count = final_text.count(target_keyword)
                    title_words = [w for w in post_title.split() if len(w) > 1]
                    missing_words = [w for w in title_words if w not in final_text]

                    with output_container.container():
                        st.success("원고 생성이 완료되었습니다! 🎉")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("공백 포함 글자 수", f"{char_count}자", delta="적정 범위" if 2000 <= char_count <= 4000 else f"확인 ({char_count}자)")
                        m2.metric("키워드 출현 횟수", f"{kw_count}회", delta="정상 (4~6회)" if 4 <= kw_count <= 6 else "수정 권장")
                        m3.metric("제목 단어 누락", f"{len(missing_words)}개", delta="전체 포함 완료" if not missing_words else f"누락: {', '.join(missing_words)}")

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
                        st.caption("👇 박스 우측 상단 네모 아이콘(📋)을 눌러도 전체 복사됩니다:")
                        st.code(final_text, language="markdown")

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
