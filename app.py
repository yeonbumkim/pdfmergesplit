# 개발자: Yeonbum Kim (yeonbumk@gmail.com)
# 2025년, MIT License
import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile
from datetime import datetime

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

# Streamlit UI
st.set_page_config(page_title='PDF 병합/분할 툴', layout='centered')
st.title('📄 PDF 병합 및 분할 웹앱')

st.sidebar.header('모드 선택')
mode = st.sidebar.radio('작업 모드', ['병합 (Merge)', '분할 (Split)'])

if mode == '병합 (Merge)':
    st.subheader('PDF 병합')
    files = st.file_uploader('여러 PDF 파일을 업로드하세요', type='pdf', accept_multiple_files=True)
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
    file = st.file_uploader('PDF 파일 1개 업로드', type='pdf', accept_multiple_files=False)
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

# 화면 하단에 개발자 정보 표시
st.markdown("""
---
<p style='text-align:center; font-size: 0.95em;'>
개발자: <b>Yeonbum Kim</b> (<a href='mailto:yeonbumk@gmail.com'>yeonbumk@gmail.com</a>)<br>
&copy; 2025 | MIT License
</p>
""", unsafe_allow_html=True) 