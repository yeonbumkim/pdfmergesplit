# 개발자: Yeonbum Kim (yeonbumk@gmail.com)
# 2025년, MIT License
import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# 페이지 범위 파싱 함수
def parse_page_ranges(range_str: str) -> list[tuple[int, int]]:
    try:
        ranges = []
        for part in range_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start), int(end)
                if start > end or start < 1:
                    raise ValueError
                ranges.append((start, end))
            else:
                num = int(part)
                if num < 1:
                    raise ValueError
                ranges.append((num, num))
        return ranges
    except Exception:
        raise ValueError('올바른 페이지 범위 형식이 아닙니다. 예: 1-3,5,7-8')

# PDF 병합 함수
def merge_pdfs(files: list) -> bytes:
    writer = PdfWriter()
    try:
        for file in files:
            reader = PdfReader(file)
            for page in reader.pages:
                writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        raise RuntimeError('PDF 병합 중 오류가 발생했습니다.')

# PDF 분할 함수
def split_pdf(file, ranges: list[tuple[int, int]]) -> dict[str, bytes]:
    result = {}
    try:
        reader = PdfReader(file)
        total_pages = len(reader.pages)
        for idx, (start, end) in enumerate(ranges, 1):
            if start < 1 or end > total_pages:
                raise ValueError('입력한 범위가 PDF 페이지 수를 벗어났습니다.')
            writer = PdfWriter()
            for i in range(start-1, end):
                writer.add_page(reader.pages[i])
            output = io.BytesIO()
            writer.write(output)
            result[f'split_{idx}_{start}-{end}.pdf'] = output.getvalue()
        return result
    except Exception as e:
        raise RuntimeError('PDF 분할 중 오류가 발생했습니다. 입력 범위를 확인하세요.')

# PDF 페이지 회전 함수
def rotate_pdf_pages(file, rotations: dict[int, int]) -> bytes:
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        for idx, page in enumerate(reader.pages, 1):
            if idx in rotations:
                page.rotate(rotations[idx])
            writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        raise RuntimeError('페이지 회전 중 오류가 발생했습니다.')

# PDF 페이지 삭제 함수
def delete_pdf_pages(file, delete_pages: list[int]) -> bytes:
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        for idx, page in enumerate(reader.pages, 1):
            if idx not in delete_pages:
                writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        raise RuntimeError('페이지 삭제 중 오류가 발생했습니다.')

# PDF 워터마크 추가 함수
def add_watermark(file, watermark_file) -> bytes:
    try:
        reader = PdfReader(file)
        watermark = PdfReader(watermark_file).pages[0]
        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(watermark)
            writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        raise RuntimeError('워터마크 추가 중 오류가 발생했습니다.')

# PDF 각 페이지를 PNG로 저장 함수
def pdf_to_pngs(file) -> dict[str, bytes]:
    from pdf2image import convert_from_bytes
    try:
        images = convert_from_bytes(file.read())
        result = {}
        for idx, img in enumerate(images, 1):
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            result[f'page_{idx}.png'] = buf.getvalue()
        return result
    except Exception:
        raise RuntimeError('PDF를 PNG로 변환 중 오류가 발생했습니다.')

# PDF 페이지 순서 변경 함수
def reorder_pdf_pages(file, new_order: list[int]) -> bytes:
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        total = len(reader.pages)
        for idx in new_order:
            if idx < 1 or idx > total:
                raise ValueError('잘못된 페이지 순서가 포함되어 있습니다.')
            writer.add_page(reader.pages[idx-1])
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        raise RuntimeError('페이지 순서 변경 중 오류가 발생했습니다.')

# --- 워터마크 텍스트용 폰트 자동 탐색 함수 ---
def get_font(fontsize=36):
    font_paths = [
        "arial.ttf",  # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "/Library/Fonts/Arial.ttf",  # Mac
        "./fonts/NanumGothic.ttf",  # 프로젝트 내 한글 폰트 예시
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, fontsize)
    return ImageFont.load_default()

# --- 워터마크 텍스트 이미지를 PDF로 변환하는 함수 ---
def create_text_watermark_pdf(
    text: str,
    width=800,
    height=300,
    angle=25,
    opacity=80,
    color=(255, 0, 0)
) -> bytes:
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    # 글씨 크기를 페이지 크기에 맞게 동적으로 조정
    font_size = int(min(width, height) * 0.12)
    font = get_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    textwidth = bbox[2] - bbox[0]
    textheight = bbox[3] - bbox[1]
    x = (width - textwidth) // 2
    y = (height - textheight) // 2
    draw.text((x, y), text, font=font, fill=color + (opacity,))
    img = img.rotate(angle, expand=1)
    buf = io.BytesIO()
    img.save(buf, format='PDF')
    return buf.getvalue()

# --- PDF에 텍스트 워터마크를 추가하는 함수 ---
def create_text_watermark_reportlab(text, width, height, color=(255,0,0), opacity=0.3, angle=25):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.saveState()
    can.setFillColorRGB(color[0]/255, color[1]/255, color[2]/255, alpha=opacity)
    can.setFont("Helvetica-Bold", int(min(width, height) * 0.12))
    can.translate(width/2, height/2)
    can.rotate(angle)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    return packet

def add_text_watermark_to_pdf(file, text, color=(255,0,0)) -> bytes:
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        watermark_pdf = create_text_watermark_reportlab(text, width, height, color=color, opacity=0.3, angle=25)
        watermark_reader = PdfReader(watermark_pdf)
        watermark_page = watermark_reader.pages[0]
        page.merge_page(watermark_page)
        writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

# PDF 암호 해제 함수 (여러 파일, 각기 다른 암호 지원)
def unlock_pdfs(files, passwords):
    results = {}
    for file, password in zip(files, passwords):
        try:
            reader = PdfReader(file)
            if reader.is_encrypted:
                # Owner Password만 있는 경우는 빈 문자열로도 해제 시도
                if password:
                    reader.decrypt(password)
                else:
                    reader.decrypt("")
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            output = io.BytesIO()
            writer.write(output)
            results[file.name] = output.getvalue()
        except Exception as e:
            results[file.name] = None  # 실패 표시
    return results

# PDF 암호 설정 함수
def encrypt_pdf(file, password):
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password=password, owner_password=None, use_128bit=True)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

# 파일 업로드 및 세션 상태 관리 함수 (widget_key와 session_key 분리)
def file_upload_with_session(session_key, widget_key, label, type='pdf', accept_multiple_files=False):
    uploaded = st.file_uploader(label, type=type, accept_multiple_files=accept_multiple_files, key=widget_key)
    if uploaded:
        st.session_state[session_key] = uploaded
    return st.session_state.get(session_key, None)

# Streamlit UI
st.set_page_config(page_title='PDF Toolbox Version 1.1', layout='centered')
st.title('📄 PDF Toolbox Version 1.1')

st.sidebar.header('모드 선택')
mode = st.sidebar.radio('작업 모드', ['병합 (Merge)', '분할 (Split)', 'PDF 편집 (Edit)'])

if mode == '병합 (Merge)':
    st.subheader('PDF 병합')
    files = file_upload_with_session('merge_files_session', 'merge_files_widget', '여러 PDF 파일을 업로드하세요', accept_multiple_files=True)
    if st.button('병합하기'):
        if not files or len(files) < 2:
            st.error('2개 이상의 PDF 파일을 업로드해주세요.')
        else:
            try:
                merged_bytes = merge_pdfs([f for f in files])
                now = datetime.now().strftime('%Y%m%d')
                st.success('병합이 완료되었습니다!')
                st.download_button(
                    label='병합된 PDF 다운로드',
                    data=merged_bytes,
                    file_name=f'merged_{now}.pdf',
                    mime='application/pdf'
                )
            except Exception as e:
                st.error(str(e))

elif mode == '분할 (Split)':
    st.subheader('PDF 분할')
    file = file_upload_with_session('split_file_session', 'split_file_widget', 'PDF 파일 1개 업로드')
    range_str = st.text_input('분할 범위 입력 (예: 1-3,5,7-8)', '')
    if st.button('분할하기'):
        if not file:
            st.error('PDF 파일을 업로드해주세요.')
        elif not range_str.strip():
            st.error('분할 범위를 입력해주세요.')
        else:
            try:
                ranges = parse_page_ranges(range_str)
                split_files = split_pdf(file, ranges)
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zipf:
                    for fname, fbytes in split_files.items():
                        zipf.writestr(fname, fbytes)
                zip_buffer.seek(0)
                now = datetime.now().strftime('%Y%m%d')
                st.success('분할이 완료되었습니다!')
                st.download_button(
                    label='분할된 PDF ZIP 다운로드',
                    data=zip_buffer,
                    file_name=f'split_{now}.zip',
                    mime='application/zip'
                )
            except Exception as e:
                st.error(str(e))

elif mode == 'PDF 편집 (Edit)':
    st.subheader('PDF 편집 기능')
    edit_file = file_upload_with_session('edit_file_session', 'edit_file_widget', 'PDF 파일 업로드')
    edit_tab = st.selectbox('기능 선택', [
        '페이지 회전',
        '페이지 삭제',
        '워터마크 추가',
        '페이지 순서 변경',
        'PDF 암호 설정',
        'PDF 암호 해제'
    ])

    if edit_tab == 'PDF 암호 설정':
        if not edit_file:
            st.warning('먼저 상단에서 PDF 파일을 업로드하세요.')
        else:
            files = edit_file if isinstance(edit_file, list) else [edit_file]
            password = st.text_input('설정할 암호를 입력하세요', type='password')
            if st.button('PDF 암호 설정'):
                if not password:
                    st.error('암호를 입력하세요.')
                else:
                    for f in files:
                        try:
                            encrypted = encrypt_pdf(f, password)
                            st.success(f"{f.name} 암호 설정 완료!")
                            st.download_button(f"{f.name} (암호설정) 다운로드", encrypted, file_name=f"encrypted_{f.name}", mime='application/pdf')
                        except Exception as e:
                            st.error(f"{f.name} 암호 설정 실패: {e}")

    elif edit_tab == 'PDF 암호 해제':
        if not edit_file:
            st.warning('먼저 상단에서 PDF 파일을 업로드하세요.')
        else:
            files = edit_file if isinstance(edit_file, list) else [edit_file]
            passwords = []
            for i, f in enumerate(files):
                pw = st.text_input(f"{f.name}의 암호 입력 (없으면 비워두세요)", key=f'unlock_pw_{i}')
                passwords.append(pw)
            if st.button('PDF 암호 해제'):
                results = unlock_pdfs(files, passwords)
                for fname, data in results.items():
                    if data:
                        st.success(f"{fname} 해제 성공!")
                        st.download_button(f"{fname} 다운로드", data, file_name=f"unlocked_{fname}", mime='application/pdf')
                    else:
                        st.error(f"{fname} 해제 실패 (암호 오류 또는 지원 불가)")

    elif edit_tab == '페이지 회전':
        st.info('예: 1:90,3:180 (1번 페이지 90도, 3번 페이지 180도 회전)')
        rotate_str = st.text_input('회전할 페이지:각도 입력', '')
        if st.button('회전 적용'):
            try:
                rotations = {}
                for part in rotate_str.split(','):
                    if ':' in part:
                        p, d = part.split(':')
                        p, d = int(p.strip()), int(d.strip())
                        if d not in [90, 180, 270]:
                            raise ValueError
                        rotations[p] = d
                rotated = rotate_pdf_pages(edit_file, rotations)
                st.success('회전 완료!')
                st.download_button('회전된 PDF 다운로드', rotated, file_name='rotated.pdf', mime='application/pdf')
            except Exception:
                st.error('입력 형식을 확인하세요. 예: 1:90,3:180')

    elif edit_tab == '페이지 삭제':
        st.info('예: 2,4 (2번, 4번 페이지 삭제)')
        del_str = st.text_input('삭제할 페이지 번호 입력', '')
        if st.button('페이지 삭제'):
            try:
                del_pages = [int(x.strip()) for x in del_str.split(',') if x.strip()]
                deleted = delete_pdf_pages(edit_file, del_pages)
                st.success('삭제 완료!')
                st.download_button('삭제된 PDF 다운로드', deleted, file_name='deleted.pdf', mime='application/pdf')
            except Exception:
                st.error('입력 형식을 확인하세요. 예: 2,4')

    elif edit_tab == '워터마크 추가':
        st.info('워터마크로 사용할 텍스트를 입력하세요. (예: Confidential)')
        watermark_text = st.text_input('워터마크 텍스트 입력', '')
        color_name = st.selectbox('워터마크 색상 선택', ['빨강', '노랑', '초록', '검정'], index=0)
        color_map = {
            '빨강': (255, 0, 0),
            '노랑': (255, 255, 0),
            '초록': (0, 128, 0),
            '검정': (0, 0, 0),
        }
        color = color_map[color_name]
        if st.button('워터마크 추가'):
            if not watermark_text.strip():
                st.error('워터마크 텍스트를 입력하세요.')
            else:
                try:
                    watermarked = add_text_watermark_to_pdf(edit_file, watermark_text, color=color)
                    st.success('워터마크 추가 완료!')
                    st.download_button('워터마크 PDF 다운로드', watermarked, file_name='watermarked.pdf', mime='application/pdf')
                except Exception as e:
                    st.error(f'워터마크 추가 중 오류가 발생했습니다: {e}')

    elif edit_tab == '페이지 순서 변경':
        st.info('예: 3,1,2 (3→1→2 순서로 재배치)')
        order_str = st.text_input('새 페이지 순서 입력', '')
        if st.button('순서 변경'):
            try:
                new_order = [int(x.strip()) for x in order_str.split(',') if x.strip()]
                reordered = reorder_pdf_pages(edit_file, new_order)
                st.success('순서 변경 완료!')
                st.download_button('순서 변경 PDF 다운로드', reordered, file_name='reordered.pdf', mime='application/pdf')
            except Exception:
                st.error('입력 형식을 확인하세요. 예: 3,1,2')

# 화면 하단에 개발자 정보 표시
st.markdown("""
---
<p style='text-align:center; font-size: 0.95em;'>
개발자: <b>Yeonbum Kim</b> (<a href='mailto:yeonbumk@gmail.com'>yeonbumk@gmail.com</a>)<br>
&copy; 2025 | MIT License
</p>
""", unsafe_allow_html=True) 