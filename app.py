import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="나음케어 계층별 리포트", layout="wide")

def clean(s): return pd.to_numeric(s.astype(str).str.replace(',', '').str.replace('"', ''), errors='coerce').fillna(0)

def extract_product_tag(group_name):
    """광고그룹명에서 #로 시작하는 마지막 태그를 상품 카테고리로 간주"""
    tags = re.findall(r'#\w+', str(group_name))
    return tags[-1] if tags else "#미분류"

def get_brand(group_name):
    """브랜드 식별"""
    brands = ['잠스트', '트라택', '빅터', '하빈져', '스포플', '엘라밴드']
    for b in brands:
        if b in str(group_name): return b
    return "기타"

st.title("📊 브랜드 > 유형 > 카테고리 계층 리포트")

with st.sidebar:
    st.header("📂 파일 업로드")
    f1 = st.file_uploader("1. 기초지표 (raw1)", type="csv")
    f2 = st.file_uploader("2. 전환지표 (raw2)", type="csv")
    f3 = st.file_uploader("3. 검색어지표 (raw3)", type="csv")

if f1 and f2:
    d1, d2 = pd.read_csv(f1, skiprows=1), pd.read_csv(f2, skiprows=1)
    d1.columns, d2.columns = d1.columns.str.strip().str.replace('"', ''), d2.columns.str.strip().str.replace('"', '')

    # 전환 데이터 피벗 및 병합
    p = d2[d2['전환 유형'] == '구매완료'].rename(columns={'총 전환수':'구매건수', '총 전환매출액(원)':'매출'})
    res = pd.merge(d1, p[['일별','캠페인','광고그룹','구매건수','매출']], on=['일별','캠페인','광고그룹'], how='left')

    for col in ['노출수','클릭수','총비용(VAT포함,원)','구매건수','매출']:
        res[col] = clean(res[col])

    # 계층 분류 생성
    res['브랜드'] = res['광고그룹'].apply(get_brand)
    res['상품카테고리'] = res['광고그룹'].apply(extract_product_tag)
    res['총비용'] = res['총비용(VAT포함,원)']
    
    # --- 브랜드 탭 (큰 탭) ---
    brand_list = [b for b in ['잠스트', '트라택', '빅터', '하빈져', '스포플', '엘라밴드', '기타'] if b in res['브랜드'].unique()]
    tabs = st.tabs(brand_list)

    for i, tab in enumerate(tabs):
        with tab:
            brand_nm = brand_list[i]
            b_df = res[res['브랜드'] == brand_nm]
            
            # 1. 브랜드 전체 요약
            c1, c2, c3 = st.columns(3)
            cost, sales = b_df['총비용'].sum(), b_df['매출'].sum()
            c1.metric("총 집행비용", f"{cost:,.0f}원")
            c2.metric("총 발생매출", f"{sales:,.0f}원")
            c3.metric("평균 ROAS", f"{(sales/cost*100 if cost>0 else 0):.1f}%")

            st.divider()

            # 2. 중간 탭: 광고유형별 합산 (파워링크, 쇼핑검색 등)
            st.subheader(f"중간분류: {brand_nm} 광고유형별")
            type_agg = b_df.groupby('캠페인유형').agg({
                '총비용':'sum', '매출':'sum', '클릭수':'sum', '구매건수':'sum'
            }).reset_index()
            type_agg['ROAS'] = (type_agg['매출']/type_agg['총비용']*100).fillna(0)
            type_agg['CPC'] = (type_agg['총비용']/type_agg['클릭수']).fillna(0)
            
            st.table(type_agg.style.format({'총비용':'{:,.0f}','매출':'{:,.0f}','ROAS':'{:.1f}%','CPC':'{:,.0f}'}))

            # 3. 하위 탭: #태그별 상품카테고리 합산
            st.subheader(f"하위분류: {brand_nm} #태그별 상세")
            cat_agg = b_df.groupby(['상품카테고리', '캠페인유형']).agg({
                '총비용':'sum', '매출':'sum', '구매건수':'sum', '클릭수':'sum'
            }).reset_index()
            cat_agg['ROAS'] = (cat_agg['매출']/cat_agg['총비용']*100).fillna(0)
            
            st.dataframe(cat_agg.sort_values('매출', ascending=False).style.format({
                '총비용':'{:,.0f}','매출':'{:,.0f}','ROAS':'{:.1f}%','클릭수':'{:,.0f}'
            }), use_container_width=True)

    # raw3 키워드 (가장 하단에 별도 유지)
    if f3:
        with st.expander("🔍 키워드별 성과 Top 30 (전체 브랜드 합산)"):
            k_df = pd.read_csv(f3, skiprows=1)
            k_df.columns = k_df.columns.str.strip().str.replace('"', '')
            st.dataframe(k_agg := k_df.groupby('검색어').agg({'총 전환매출액(원)':'sum','클릭수':'sum'}).sort_values('총 전환매출액(원)', ascending=False).head(30))
