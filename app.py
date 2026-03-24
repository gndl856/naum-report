import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="나음케어 브랜드 리포트", layout="wide")

def clean(s): return pd.to_numeric(s.astype(str).str.replace(',', '').str.replace('"', ''), errors='coerce').fillna(0)

def get_brand(group_name):
    """#태그 중 브랜드명만 추출 (가장 앞의 태그 활용)"""
    tags = re.findall(r'#\w+', str(group_name))
    if not tags: return "기타/미분류"
    # 브랜드 대표 태그 추출 (잠스트, 트라택, 빅터, 하빈져 등)
    brands = ['잠스트', '트라택', '빅터', '하빈져', '스포플', '엘라밴드']
    for t in tags:
        for b in brands:
            if b in t: return b
    return tags[0] # 지정된 브랜드가 없으면 첫 태그 반환

st.title("🏷️ 브랜드별 통합 분석 대시보드")

with st.sidebar:
    st.header("📂 리포트 업로드")
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

    # 브랜드 분류 및 지표 계산
    res['브랜드'] = res['광고그룹'].apply(get_brand)
    res['총비용'] = res['총비용(VAT포함,원)']
    
    # --- 브랜드 탭 생성 ---
    brand_list = sorted(res['브랜드'].unique())
    tabs = st.tabs(brand_list)

    for i, tab in enumerate(tabs):
        with tab:
            target_brand = brand_list[i]
            b_data = res[res['브랜드'] == target_brand]
            
            # 브랜드 요약 수치
            m1, m2, m3, m4 = st.columns(4)
            cost = b_data['총비용'].sum()
            sales = b_data['매출'].sum()
            roas = (sales/cost*100) if cost > 0 else 0
            m1.metric("총 비용", f"{cost:,.0f}원")
            m2.metric("총 매출", f"{sales:,.0f}원")
            m3.metric("ROAS", f"{roas:.1f}%")
            m4.metric("구매건수", f"{b_data['구매건수'].sum():,.0f}건")

            # 브랜드 내 광고유형별 성과
            st.markdown(f"#### 💡 {target_brand} 유형별/카테고리별 성과")
            agg = b_data.groupby(['캠페인유형', '광고그룹']).agg({
                '총비용':'sum', '매출':'sum', '클릭수':'sum', '구매건수':'sum', '장바구니건수':'sum'
            }).reset_index()
            agg['ROAS'] = (agg['매출']/agg['총비용']*100).fillna(0)
            
            st.dataframe(agg.sort_values('매출', ascending=False).style.format({
                '총비용':'{:,.0f}','매출':'{:,.0f}','ROAS':'{:.1f}%','클릭수':'{:,.0f}'
            }), use_container_width=True)

    # raw3 키워드 분석 (별도 섹션)
    if f3:
        with st.expander("🔍 전체 브랜드 주요 검색어 순위 (Top 50)"):
            d3 = pd.read_csv(f3, skiprows=1)
            d3.columns = d3.columns.str.strip().str.replace('"', '')
            k_agg = d3.groupby('검색어').agg({'노출수':'sum','클릭수':'sum','총 전환매출액(원)':'sum'}).sort_values('총 전환매출액(원)', ascending=False).head(50)
            st.table(k_agg)
