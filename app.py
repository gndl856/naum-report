import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="나음케어 통합 리포트", layout="wide")

def clean(s): return pd.to_numeric(s.astype(str).str.replace(',', '').str.replace('"', ''), errors='coerce').fillna(0)

def extract_tags(group_name):
    """광고그룹명에서 #로 시작하는 태그들 추출"""
    return re.findall(r'#\w+', str(group_name))

st.title("📊 나음케어 멀티 차원 분석 리포트")

with st.sidebar:
    st.header("📂 파일 업로드")
    f1 = st.file_uploader("1. 기초지표 (raw1)", type="csv")
    f2 = st.file_uploader("2. 전환지표 (raw2)", type="csv")
    f3 = st.file_uploader("3. 검색어지표 (raw3)", type="csv")

if f1 and f2:
    # 데이터 로드 및 전처리
    d1, d2 = pd.read_csv(f1, skiprows=1), pd.read_csv(f2, skiprows=1)
    d1.columns, d2.columns = d1.columns.str.strip().str.replace('"', ''), d2.columns.str.strip().str.replace('"', '')

    p = d2[d2['전환 유형'] == '구매완료'].rename(columns={'총 전환수':'구매건수', '총 전환매출액(원)':'매출'})
    c = d2[d2['전환 유형'] == '장바구니 담기'].rename(columns={'총 전환수':'장바구니건수', '총 전환매출액(원)':'장바구니매출'})

    res = pd.merge(d1, p[['일별','캠페인','광고그룹','구매건수','매출']], on=['일별','캠페인','광고그룹'], how='left')
    res = pd.merge(res, c[['일별','캠페인','광고그룹','장바구니건수','장바구니매출']], on=['일별','캠페인','광고그룹'], how='left')

    for col in ['노출수','클릭수','총비용(VAT포함,원)','구매건수','매출','장바구니건수','장바구니매출']:
        if col in res.columns: res[col] = clean(res[col])

    # 브랜드 및 카테고리 추출 로직
    res['태그리스트'] = res['광고그룹'].apply(extract_tags)
    # 첫 번째 태그를 브랜드/카테고리로 가정 (데이터에 맞춰 자동 분류)
    res['주요분류'] = res['태그리스트'].apply(lambda x: x[0] if len(x) > 0 else "#미분류")

    # 지표 계산
    res['총비용'] = res['총비용(VAT포함,원)']
    res['ROAS'] = (res['매출']/res['총비용']*100).fillna(0)
    
    # --- UI 탭 구성 ---
    tab1, tab2, tab3 = st.tabs(["1. 광고유형별", "2. 브랜드/태그별", "3. 상세 데이터"])

    with tab1:
        st.subheader("💡 광고유형별 성과 (파워링크/쇼핑검색 등)")
        type_agg = res.groupby('캠페인유형').agg({
            '총비용':'sum', '매출':'sum', '노출수':'sum', '클릭수':'sum', '구매건수':'sum'
        })
        type_agg['ROAS'] = (type_agg['매출']/type_agg['총비용']*100).fillna(0)
        st.dataframe(type_agg.style.format({'총비용':'{:,.0f}','매출':'{:,.0f}','ROAS':'{:.1f}%'}))

    with tab2:
        st.subheader("🏷️ 브랜드 및 상품 카테고리별 성과 (#태그 기준)")
        tag_agg = res.groupby(['주요분류', '캠페인유형']).agg({
            '총비용':'sum', '매출':'sum', '구매건수':'sum', '클릭수':'sum'
        }).reset_index()
        tag_agg['ROAS'] = (tag_agg['매출']/tag_agg['총비용']*100).fillna(0)
        st.dataframe(tag_agg.sort_values('매출', ascending=False).style.format({'총비용':'{:,.0f}','매출':'{:,.0f}','ROAS':'{:.1f}%'}))

    with tab3:
        if f3:
            st.subheader("🔍 주요 키워드별 성과 (raw3 기준)")
            d3 = pd.read_csv(f3, skiprows=1)
            d3.columns = d3.columns.str.strip().str.replace('"', '')
            keyword_agg = d3.groupby('검색어').agg({
                '노출수':'sum', '클릭수':'sum', '총 전환수':'sum', '총 전환매출액(원)':'sum'
            }).sort_values('총 전환매출액(원)', ascending=False).head(50)
            st.dataframe(keyword_agg.style.format({'총 전환매출액(원)':'{:,.0f}'}))
        else:
            st.warning("키워드 분석을 보려면 raw3 파일을 업로드하세요.")
