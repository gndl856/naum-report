import streamlit as st
import pandas as pd

st.set_page_config(page_title="나음케어 리포트", layout="wide")

def clean(s): return pd.to_numeric(s.astype(str).str.replace(',', '').str.replace('"', ''), errors='coerce').fillna(0)

st.title("📊 나음케어 성과 분석 리포트")

with st.sidebar:
    f1 = st.file_uploader("raw1 (기초)", type="csv")
    f2 = st.file_uploader("raw2 (전환)", type="csv")
    f3 = st.file_uploader("raw3 (검색어)", type="csv")

if f1 and f2:
    d1, d2 = pd.read_csv(f1, skiprows=1), pd.read_csv(f2, skiprows=1)
    d1.columns, d2.columns = d1.columns.str.strip().str.replace('"', ''), d2.columns.str.strip().str.replace('"', '')

    p = d2[d2['전환 유형'] == '구매완료'].rename(columns={'총 전환수':'구매건수', '총 전환매출액(원)':'매출'})
    c = d2[d2['전환 유형'] == '장바구니 담기'].rename(columns={'총 전환수':'장바구니건수', '총 전환매출액(원)':'장바구니매출'})

    res = pd.merge(d1, p[['일별','캠페인','광고그룹','구매건수','매출']], on=['일별','캠페인','광고그룹'], how='left')
    res = pd.merge(res, c[['일별','캠페인','광고그룹','장바구니건수','장바구니매출']], on=['일별','캠페인','광고그룹'], how='left')

    for col in ['노출수','클릭수','총비용(VAT포함,원)','구매건수','매출','장바구니건수','장바구니매출']:
        res[col] = clean(res[col])

    res['총비용'] = res['총비용(VAT포함,원)']
    res['ROAS'] = (res['매출']/res['총비용']*100).fillna(0)
    res['구매율'] = (res['구매건수']/res['클릭수']*100).fillna(0)
    res['CPC'] = (res['총비용']/res['클릭수']).fillna(0)
    res['장바구니율'] = (res['장바구니건수']/res['클릭수']*100).fillna(0)

    cols = ['일별','캠페인','광고그룹','총비용','매출','ROAS','구매율','CPC','노출수','클릭수','장바구니건수','장바구니매출','장바구니율']
    st.dataframe(res[cols].style.format({'총비용':'{:,.0f}','매출':'{:,.0f}','ROAS':'{:.1f}%','구매율':'{:.2f}%','CPC':'{:,.0f}','노출수':'{:,.0f}','클릭수':'{:,.0f}','장바구니율':'{:.2f}%'}), use_container_width=True)
