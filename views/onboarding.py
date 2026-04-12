import streamlit as st


def render():
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 20px 0;">
        <div style="font-size:13px; font-weight:700; color:#3d6af5;
                    letter-spacing:0.18em; text-transform:uppercase; margin-bottom:10px;">
            REGALITH INTELLIGENCE
        </div>
        <div style="font-size:26px; font-weight:700; color:#e8edf5; margin-bottom:8px;">
            Configure your company profile
        </div>
        <div style="font-size:13px; color:#5a7090; max-width:480px; margin:0 auto;">
            Regalith maps regulation onto your specific operating model.
            Answer a few questions to calibrate the impact analysis.
        </div>

        <!-- Step indicator -->
        <div style="display:flex; align-items:center; justify-content:center;
                    gap:0; margin: 28px auto 0; max-width:320px;">
            <!-- Step 1 -->
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
                <div style="width:28px; height:28px; border-radius:50%;
                            background:#3d6af5; color:#ffffff;
                            font-size:12px; font-weight:700;
                            display:flex; align-items:center; justify-content:center;">
                    1
                </div>
                <div style="font-size:10px; font-weight:600; color:#3d6af5;
                            letter-spacing:0.08em; text-transform:uppercase;">
                    Company profile
                </div>
            </div>
            <!-- Connector -->
            <div style="flex:1; height:2px; background:#1e2d4a;
                        margin: 0 12px; margin-bottom:20px;"></div>
            <!-- Step 2 -->
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
                <div style="width:28px; height:28px; border-radius:50%;
                            background:#1e2d4a; color:#4a6080;
                            font-size:12px; font-weight:700;
                            display:flex; align-items:center; justify-content:center;">
                    2
                </div>
                <div style="font-size:10px; font-weight:600; color:#4a6080;
                            letter-spacing:0.08em; text-transform:uppercase;">
                    Intelligence layer
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_form, col_r = st.columns([1, 3, 1])
    with col_form:
        with st.form("onboarding_form"):
            company_name = st.text_input(
                "Company name",
                placeholder="e.g. PayNow sp. z o.o."
            )

            license_type = st.selectbox(
                "Licence type",
                ["EMI", "PI", "VASP", "Bank", "Lending"],
                help="Electronic Money Institution, Payment Institution, Crypto Asset Service Provider, Bank, or Lending"
            )

            col1, col2 = st.columns(2)
            with col1:
                jurisdictions = st.multiselect(
                    "Jurisdictions of operation",
                    ["Poland", "EU-wide", "Germany", "France", "Netherlands", "Lithuania", "UK", "Other"],
                    default=["Poland"]
                )
            with col2:
                products = st.multiselect(
                    "Products offered",
                    ["E-wallet", "Card issuing", "Remittance / FX", "Crypto exchange",
                     "Crypto custody", "BNPL", "Consumer lending", "SME lending",
                     "Payment gateway", "Open banking"],
                    default=["E-wallet", "Card issuing"]
                )

            col3, col4 = st.columns(2)
            with col3:
                customer_segments = st.multiselect(
                    "Customer segments",
                    ["Retail B2C", "SME", "Corporate", "Crypto-native users"],
                    default=["Retail B2C"]
                )
            with col4:
                headcount_range = st.selectbox(
                    "Headcount",
                    ["<20", "20–100", "100–500", "500+"]
                )

            col5, col6 = st.columns(2)
            with col5:
                monthly_volume = st.selectbox(
                    "Monthly onboarding volume",
                    ["<1,000 / month", "1,000–10,000 / month",
                     "10,000–100,000 / month", "100,000+ / month"]
                )
            with col6:
                outsourced_kyc = st.selectbox(
                    "KYC / AML function",
                    ["In-house", "Outsourced to vendor", "Hybrid"],
                )

            col7, col8 = st.columns(2)
            with col7:
                has_remote = st.checkbox("Remote / digital-only onboarding", value=True)
            with col8:
                has_crypto = st.checkbox("Crypto products in scope", value=False)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            submitted = st.form_submit_button("Activate intelligence layer →", use_container_width=True)

        if submitted:
            if not company_name.strip():
                st.error("Please enter your company name.")
                return

            st.session_state["profile"] = {
                "company_name": company_name.strip(),
                "license_type": license_type,
                "jurisdictions": jurisdictions,
                "products": products,
                "customer_segments": customer_segments,
                "headcount_range": headcount_range,
                "monthly_onboarding_volume": monthly_volume,
                "outsourced_kyc": outsourced_kyc,
                "has_remote_onboarding": has_remote,
                "has_crypto": has_crypto,
            }
            st.session_state["view"] = "results"
            st.rerun()
