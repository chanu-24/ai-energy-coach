# Streamlit App Code Saved Successfully
import streamlit as st
import os
from openai import OpenAI

# OpenAI 클라이언트 설정 (Streamlit Secrets에서 키를 자동으로 가져옵니다)
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

st.title("⚡ 소상공인 AI 에너지 코치")
st.write("매장 에너지 사용량을 입력하고 맞춤형 코칭을 받아보세요!")

# 간단한 입력 폼
monthly_bill = st.number_input("이번 달 전기요금 (원)", min_value=0, value=300000)
business_type = st.selectbox("업종 선택", ["음식점/카페", "소매점/상점", "기타"])

if st.button("에너지 절감 진단 및 코칭 받기"):
    with st.spinner("AI 코치가 분석 중입니다..."):
        try:
            # 간단한 절감액 계산 로직 (예시)
            estimated_savings = monthly_bill * 0.15
            
            st.success(f"예상 절감 금액: 약 {int(estimated_savings):,}원 / 월")
            
            # OpenAI API를 이용한 LLM 코칭
            prompt = f"업종이 {business_type}이고 월 전기요금이 {monthly_bill:,}원인 소상공인에게 실질적인 에너지 절감 팁 3가지를 친절하게 코칭해줘."
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            coach_advice = response.choices[0].message.content
            st.subheader("💡 AI 에너지 코칭 리포트")
            st.write(coach_advice)
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")