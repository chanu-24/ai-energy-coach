# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: 해커튼 팀 실행안(5대 핵심 개선 항목) 기반 스펙 및 계산 파이프라인
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        {"equipment": "FRAME", "name": "🎮 게임 프레임 설정 (전력 최적화)", "rated_power_kw": 0.03, "default_hours": 8},
        {"equipment": "UPDATE_BEFORE", "name": "⏳ 업데이트 전 대기 관리", "rated_power_kw": 0.08, "default_hours": 2},
        {"equipment": "UPDATE_AFTER", "name": "🛑 업데이트 후 방치 관리", "rated_power_kw": 0.08, "default_hours": 3},
        {"equipment": "ZONE_OP", "name": "💡❄️ 저이용 시간 구역별 조명·냉방 운영", "rated_power_kw": 1.0, "default_hours": 6},
        {"equipment": "PERIPHERAL", "name": "⌨️ 게이밍 주변기기 조명 관리", "rated_power_kw": 0.002, "default_hours": 10}
    ])
    return equipment_df

def calculate_detailed_impact(answers, equipment_df):
    CARBON_FACTOR = 0.4781
    KRW_PER_KWH = 130.0 
    
    pc_count = answers.get("pc_count", 50)
    
    # 기획서 기준 공식에 따른 정밀 계산
    before_results = []
    after_results = []
    
    for _, row in equipment_df.iterrows():
        eq = row["equipment"]
        
        if eq == "FRAME":
            frame_ans = answers.get("q2_frame", "제한하지 않음")
            w_map = {"매장 공통 제한": 0.0, "게임별 제한": 0.1, "제한하지 않음": 1.0, "모름": 1.0}
            factor = w_map.get(frame_ans, 1.0)
            
            b_kwh = row["rated_power_kw"] * pc_count * 8 * 30 * factor
            a_kwh = b_kwh * 0.1 # 제한 시 대폭 감소
            
        elif eq == "UPDATE_BEFORE":
            up_b_ans = answers.get("q3_update_before", "계속 켜둠")
            w_map = {"업데이트 직전에 컴": 0.0, "시작 전 일정 시간 켜둠": 0.5, "계속 켜둠": 1.0, "해당 없음·모름": 0.8}
            factor = w_map.get(up_b_ans, 1.0)
            
            b_kwh = row["rated_power_kw"] * pc_count * 2 * 20 * factor
            a_kwh = b_kwh * 0.1
            
        elif eq == "UPDATE_AFTER":
            up_a_ans = answers.get("q4_update_after", "다음 손님까지 켜둠")
            w_map = {"자동 종료·절전": 0.0, "직원이 종료": 0.3, "다음 손님까지 켜둠": 1.0, "해당 없음·모름": 0.8}
            factor = w_map.get(up_a_ans, 1.0)
            
            b_kwh = row["rated_power_kw"] * pc_count * 3 * 20 * factor
            a_kwh = b_kwh * 0.1
            
        elif eq == "ZONE_OP":
            zone_ans = answers.get("q5_zone", "매장 전체 자유 이용")
            w_map = {"특정 구역 우선 안내": 0.1, "일부 구역만 운영": 0.3, "매장 전체 자유 이용": 1.0, "모름": 1.0}
            factor = w_map.get(zone_ans, 1.0)
            
            b_kwh = row["rated_power_kw"] * 6 * 30 * factor
            a_kwh = b_kwh * 0.1
            
        else: # PERIPHERAL (주변기기 조명)
            peri_ans = answers.get("q6_peripheral", "대부분 켜짐")
            w_map = {"모두 꺼짐": 0.0, "일부 켜짐": 0.5, "대부분 켜짐": 1.0, "모름": 1.0}
            factor = w_map.get(peri_ans, 1.0)
            
            b_kwh = row["rated_power_kw"] * pc_count * 10 * 30 * factor
            a_kwh = b_kwh * 0.1

        b_cost = b_kwh * KRW_PER_KWH
        a_cost = a_kwh * KRW_PER_KWH
        b_carbon = b_kwh * CARBON_FACTOR
        a_carbon = a_kwh * CARBON_FACTOR
        
        before_results.append({"equipment": eq, "name": row["name"], "kwh": round(b_kwh, 1), "cost": round(b_cost), "carbon": round(b_carbon, 1)})
        after_results.append({"equipment": eq, "name": row["name"], "kwh": round(a_kwh, 1), "cost": round(a_cost), "carbon": round(a_carbon, 1)})
        
    return pd.DataFrame(before_results), pd.DataFrame(after_results)

# 2. 백엔드: Python Rule Engine
def python_rule_engine(answers):
    diagnoses = []
    
    if answers.get("q2_frame") == "제한하지 않음":
        diagnoses.append({
            "title": "🎮 게임 최대 프레임 수 미제한",
            "description": "불필요하게 높은 프레임으로 GPU 및 CPU 연산 전력이 과다 소모되고 있습니다. 최대 프레임을 제한하여 전력을 절감하세요.",
            "equipment": "FRAME", "risk_score": 90
        })
    if answers.get("q3_update_before") == "계속 켜둠":
        diagnoses.append({
            "title": "⏳ 게임 업데이트 전 대기 시간 동안 PC 상시 대기",
            "description": "업데이트 시작 전부터 빈 좌석의 PC를 켜둔 채 방치하여 대기전력이 낭비되고 있습니다.",
            "equipment": "UPDATE_BEFORE", "risk_score": 85
        })
    if answers.get("q4_update_after") in ["다음 손님까지 켜둠", "직원이 종료"]:
        diagnoses.append({
            "title": "🛑 업데이트 완료 후 빈 좌석 PC 방치",
            "description": "업데이트가 끝났음에도 다음 손님이 올 때까지 PC가 켜져 있어 전기가 계속 소모됩니다.",
            "equipment": "UPDATE_AFTER", "risk_score": 85
        })
    if answers.get("q5_zone") == "매장 전체 자유 이용":
        diagnoses.append({
            "title": "💡❄️ 저이용 시간 구역 미분리 및 전체 운영",
            "description": "손님이 적은 시간에도 매장 전체에 조명과 냉방을 가동하여 전력 손실이 발생합니다.",
            "equipment": "ZONE_OP", "risk_score": 80
        })
    if answers.get("q6_peripheral") in ["대부분 켜짐", "일부 켜짐"]:
        diagnoses.append({
            "title": "⌨️ 미사용 좌석 게이밍 주변기기 조명 상시 점등",
            "description": "손님이 없는 좌석의 키보드·마우스·헤드셋 거치대 조명이 계속 켜져 있습니다.",
            "equipment": "PERIPHERAL", "risk_score": 60
        })
        
    if not diagnoses:
        diagnoses.append({
            "title": "✨ 우수한 에너지 관리 상태",
            "description": "해커튼 팀 실행안의 주요 절감 지침을 잘 준수하고 있습니다.",
            "equipment": "FRAME", "risk_score": 30
        })
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

# 3. 백엔드: ChromaDB RAG
@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_energy_guide")
    if col.count() == 0:
        col.add(ids=["doc_1"], documents=["[실행안 가이드] 게임 프레임 제한: 메뉴 및 백그라운드부터 검토하여 대당 30W 이상 절감."], metadatas=[{"equipment": "FRAME"}])
        col.add(ids=["doc_2"], documents=["[실행안 가이드] 업데이트 전 대기: 작업 직전에만 PC를 켜고 불필요한 대기시간 2시간 단축."], metadatas=[{"equipment": "UPDATE_BEFORE"}])
        col.add(ids=["doc_3"], documents=["[실행안 가이드] 업데이트 후 방치: 작업 완료 상태 기준 자동 절전/종료 설정."], metadatas=[{"equipment": "UPDATE_AFTER"}])
        col.add(ids=["doc_4"], documents=["[실행안 가이드] 구역별 운영: 저이용 시간에 특정 구역 우선 안내 및 독립 조명·냉방 제어."], metadatas=[{"equipment": "ZONE_OP"}])
        col.add(ids=["doc_5"], documents=["[실행안 가이드] 주변기기 조명: 미사용 시 조명 끄기 또는 밝기 낮추기 연동."], metadatas=[{"equipment": "PERIPHERAL"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(eq):
    results = rag_collection.query(query_texts=["에너지 절감 가이드"], n_results=1, where={"equipment": eq})
    return results["documents"][0][0] if results["documents"] else "관련 공식 가이드가 없습니다."

# 4. 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {
        "pc_count": 50,
        "q2_frame": "제한하지 않음",
        "q3_update_before": "계속 켜둠",
        "q4_update_after": "다음 손님까지 켜둠",
        "q5_zone": "매장 전체 자유 이용",
        "q6_peripheral": "대부분 켜짐"
    }

# [페이지 1] 해커튼 팀 실행안 기반 5대 핵심 질문 폼
if st.session_state.step == 1:
    st.title("⚡ PC방 전력 사용 개선 자가진단")
    st.write("해커튼 팀 공유용 실행안에 따른 5대 핵심 전력 개선 문항입니다.")
    
    with st.form("survey_team_form"):
        pc_count = st.number_input("매장 총 PC 대수", min_value=10, max_value=300, value=st.session_state.answers.get("pc_count", 50), step=10)
        
        st.subheader("2. 게임 프레임 설정")
        q2_frame = st.radio("게임의 최대 프레임 수를 제한해 두셨나요?", ["매장 공통 제한", "게임별 제한", "제한하지 않음", "모름"])
        
        st.subheader("3. 업데이트 전 대기")
        q3_update_before = st.radio("게임 업데이트를 기다리는 동안 빈 좌석 PC를 미리 켜두시나요?", ["업데이트 직전에 컴", "시작 전 일정 시간 켜둠", "계속 켜둠", "해당 없음·모름"])
        
        st.subheader("4. 업데이트 후 방치")
        q4_update_after = st.radio("게임 업데이트가 끝난 빈 좌석 PC는 어떻게 처리하시나요?", ["자동 종료·절전", "직원이 종료", "다음 손님까지 켜둠", "해당 없음·모름"])
        
        st.subheader("5. 손님이 적은 시간의 좌석 운영")
        q5_zone = st.radio("손님이 적은 시간에는 좌석을 특정 구역으로 안내하시나요?", ["특정 구역 우선 안내", "일부 구역만 운영", "매장 전체 자유 이용", "모름"])
        
        st.subheader("6. 게이밍 주변기기 조명")
        q6_peripheral = st.radio("손님이 없는 좌석에서도 키보드·마우스·헤드셋 거치대 조명이 계속 켜져 있나요?", ["모두 꺼짐", "일부 켜짐", "대부분 켜짐", "모름"])

        submitted = st.form_submit_button("실행안 맞춤형 AI 진단하기 🚀", use_container_width=True)
        if submitted:
            st.session_state.answers = {
                "pc_count": pc_count,
                "q2_frame": q2_frame,
                "q3_update_before": q3_update_before,
                "q4_update_after": q4_update_after,
                "q5_zone": q5_zone,
                "q6_peripheral": q6_peripheral
            }
            st.session_state.step = 2
            st.rerun()

# [페이지 2] AI 에너지 진단 결과
elif st.session_state.step == 2:
    st.title("🔍 AI 에너지 진단 결과 (실행안 기반)")
    diagnoses = python_rule_engine(st.session_state.answers)
    
    max_risk = max([d["risk_score"] for d in diagnoses]) if diagnoses else 40
    efficiency_score = max(30, int(100 - (max_risk * 0.7)))
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="실행안 전력 효율 점수", value=f"{efficiency_score}점", delta="개선 필요" if efficiency_score < 70 else "우수함", delta_color="inverse")
    with col2:
        st.info("💡 해커튼 팀 실행안 기준에 따른 매장 전력 낭비 요인 분석 결과입니다.")
        
    st.subheader("🚨 우선 개선 영역 및 가이드 (Rule Engine + RAG)")
    for diag in diagnoses:
        guide = search_rag_guides(diag["equipment"])
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;">
            <h4>{diag['title']} <span style="color:#ef4444; font-size:12px;">[위험점수: {diag['risk_score']}]</span></h4>
            <p style="color:#475569; margin:5px 0;">{diag['description']}</p>
            <hr style="margin:8px 0; border:0; border-top:1px solid #cbd5e1;">
            <p style="font-size:13px; color:#047857; margin:0;"><b>📘 팀 실행안 가이드:</b> {guide}</p>
        </div>
        """, unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 설문 수정하기", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with c2:
        if st.button("📈 상세 절감액 분석 보기 ➔", use_container_width=True):
            st.session_state.step = 3; st.rerun()

# [페이지 3] 예상 전력절감 및 감액가능 상세 분석
elif st.session_state.step == 3:
    pc_count_val = st.session_state.answers.get("pc_count", 50)
    st.title(f"📈 항목별 예상 전력절감 및 감액 분석 ({pc_count_val}석 기준)")
    st.write("해커튼 팀 실행안의 절감 예시 공식에 따른 월간 절감 효과입니다.")
    
    eq_df = load_pc_bang_data()
    b_df, a_df = calculate_detailed_impact(st.session_state.answers, eq_df)
    
    tot_b_kwh, tot_a_kwh = b_df["kwh"].sum(), a_df["kwh"].sum()
    tot_b_cost, tot_a_cost = b_df["cost"].sum(), a_df["cost"].sum()
    tot_b_carb, tot_a_carb = b_df["carbon"].sum(), a_df["carbon"].sum()
    
    saved_cost = int(tot_b_cost - tot_a_cost)
    saved_kwh = int(tot_b_kwh - tot_a_kwh)
    saved_carb = round(tot_b_carb - tot_a_carb, 1)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">총 전력절감량</div>
            <div style="font-size:24px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_kwh:,} kWh</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">전기요금 감액금액</div>
            <div style="font-size:24px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_cost:,} 원</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">탄소 감축량</div>
            <div style="font-size:24px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_carb} kg</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("🔍 실행안 항목별 상세 절감 내역")
    
    for i in range(len(b_df)):
        name = b_df.loc[i, "name"]
        b_kwh, a_kwh = b_df.loc[i, "kwh"], a_df.loc[i, "kwh"]
        b_cost, a_cost = b_df.loc[i, "cost"], a_df.loc[i, "cost"]
        diff_kwh = round(b_kwh - a_kwh, 1)
        diff_cost = int(b_cost - a_cost)
        
        st.markdown(f"""
        <div style="background-color:#f1f5f9; border-left:5px solid #3b82f6; padding:15px; border-radius:8px; margin-bottom:12px;">
            <h4 style="margin:0 0 8px 0; color:#1e293b;">{name}</h4>
            <p style="margin:4px 0; font-size:14px; color:#334155;">
               • <b>전력 변화:</b> <span style="color:#dc2626;">{b_kwh:,.1f} kWh</span> ➔ <span style="color:#16a34a;">{a_kwh:,.1f} kWh</span> (<b>총 {diff_kwh:,.1f} kWh 절감</b>)
            </p>
            <p style="margin:4px 0; font-size:14px; color:#334155;">
               • <b>요금 변화:</b> <span style="color:#dc2626;">{b_cost:,} 원</span> ➔ <span style="color:#16a34a;">{a_cost:,} 원</span> (<b>총 {diff_cost:,} 원 감액</b>)
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 항목별 비교 요약 테이블")
    comparison_df = pd.DataFrame({
        "개선 항목": b_df["name"],
        "기존 전력": b_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "개선 후 전력": a_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "기존 요금": b_df["cost"].apply(lambda x: f"{x:,} 원"),
        "개선 후 요금": a_df["cost"].apply(lambda x: f"{x:,} 원"),
        "월 절감 금액": (b_df["cost"] - a_df["cost"]).apply(lambda x: f"{int(x):,} 원")
    })
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()