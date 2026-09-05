import base64
from datetime import datetime
import os
import jinja2
import requests
import streamlit as st
import streamlit.components.v1 as components
import weasyprint

# 1. பக்க கட்டமைப்பு
st.set_page_config(
    page_title="MGP Gold Takeover Cloud", page_icon="🪙", layout="wide"
)

# 2. மேல் வலதுபுற மெனு மற்றும் பிற தேவையில்லாத ஐகான்களை மறைக்கும் CSS
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    [data-testid="stToolbar"] {visibility: hidden; display: none;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 3. கிளை அணுகல் கடவுச்சொல் (PIN Protection)
BRANCH_PIN = "1234"

if "authenticated" not in st.session_state:
  st.session_state.authenticated = False

if not st.session_state.authenticated:
  st.markdown("### 🔒 முத்துசிஸ் கோல்டு - கிளை ஊழியர் உள்நுழைவு")
  entered_pin = st.text_input(
      "கிளை அணுகல் PIN எண்ணை உள்ளிடவும்:", type="password", max_chars=6
  )
  if st.button("உள்நுழைக (Login)"):
    if entered_pin == BRANCH_PIN:
      st.session_state.authenticated = True
      st.rerun()
    else:
      st.error("தவறான PIN எண்! தயவுசெய்து சரியான எண்ணை உள்ளிடவும்.")
  st.stop()

# 4. முதன்மைத் திரை & ஆவண வகை தேர்வு
st.title("🪙 முத்துசிஸ் கோல்டு புராடக்ட் பி.லிட் - அடகு நகை மீட்புக் கோப்பு அமைப்பு")
st.caption("கிளைகளுக்கான ஒருங்கிணைந்த ஆவணத் தொகுப்பு உருவாக்க இணையதளம்")
st.markdown("---")

with st.form("cloud_takeover_form", clear_on_submit=False):
  st.subheader("📑 தேவையான ஆவண வகையைத் தேர்ந்தெடுக்கவும்")
  doc_choice = st.radio(
      "ஆவண மாதிரி (Document Format):",
      [
          "குறைந்த தொகைக்கான எளிய படிவம் (ரூ. 1 ரெவென்யூ ஸ்டாம்ப்)",
          "உயர் மதிப்பு 5 பக்க முழு கோப்பு (நான்-ஜுடிசியல் முத்திரைத்தாள்)",
      ],
      index=0,
      horizontal=True,
  )

  st.markdown("---")
  st.subheader("1. வாடிக்கையாளர் விபரம் (Customer Information)")
  col1, col2, col3 = st.columns(3)
  with col1:
    customer_name = st.text_input("வாடிக்கையாளர் பெயர் *")
    customer_guardian = st.text_input("தந்தை / கணவர் பெயர் *")
  with col2:
    customer_phone = st.text_input("கைபேசி எண் *", max_chars=10)
    customer_aadhaar = st.text_input("ஆதார் எண் *", max_chars=14)
  with col3:
    customer_pan = st.text_input("பான் எண்", max_chars=10)
    customer_address = st.text_area("முகவரி", height=68)

  st.subheader("2. வங்கி & கடன் விபரம் (Bank & Pledge Details)")
  col4, col5, col6 = st.columns(3)
  with col4:
    bank_name = st.text_input("அடகு வைத்துள்ள வங்கி / நிறுவனம் *")
    bank_branch = st.text_input("வங்கி கிளை *")
  with col5:
    loan_acc_no = st.text_input("நகைக்கடன் கணக்கு எண் *")
    pledge_receipt_no = st.text_input("அடகு ரசீது எண்")
  with col6:
    gross_weight = st.number_input(
        "மொத்த எடை (கிராம்) *", min_value=1.0, max_value=2000.0, step=0.5
    )
    time_limit = st.selectbox(
        "மீட்பு நேர வரம்பு (மணி நேரம்)", ["2", "3", "4", "6"], index=0
    )

  st.subheader("3. முன்பணம் & பாதுகாப்புக் காசோலை (Payment & Security Cheque)")
  col7, col8, col9 = st.columns(3)
  with col7:
    advance_amount = st.number_input(
        "மீட்பு முன்பணத் தொகை (ரூ.) *", min_value=1000, step=1000, format="%d"
    )
  with col8:
    utr_no = st.text_input("வங்கி UTR Ref எண் (இருப்பின் மட்டும் நிரப்பவும்)", "")
    branch_name = st.selectbox(
        "பரிவர்த்தனை செய்யும் நமது கிளை *",
        ["நாகர்கோவில் (HQ)", "திங்கள்நகர்", "பிற கிளைகள்"],
    )
  with col9:
    cheque_bank = st.text_input("காசோலை வங்கி பெயர்")
    cheque_no = st.text_input("காசோலை எண்")

  submitted = st.form_submit_button(
      "🖨️ சேமித்து நேரடியாக அச்சிடுக (Save & Direct Print)",
      use_container_width=True,
  )

# 5. செயலாக்கம் மற்றும் நேரடி அச்சு
if submitted:
  if not customer_name or not bank_name or not loan_acc_no or not advance_amount:
    st.error("தயவுசெய்து நட்சத்திரக் குறியிட்ட (*) கட்டாய விவரங்களை நிரப்பவும்!")
  else:
    now = datetime.now()
    docket_no = f"MGP-TO-{now.strftime('%Y%m%d%H%M%S')}"
    txn_date = now.strftime("%d/%m/%Y")
    txn_time = now.strftime("%I:%M %p")

    display_utr = (
        utr_no.strip() if utr_no.strip() else "___________________________"
    )

    context = {
        "docket_no": docket_no,
        "txn_date": txn_date,
        "txn_time": txn_time,
        "customer_name": customer_name,
        "customer_guardian": customer_guardian,
        "customer_phone": customer_phone,
        "customer_aadhaar": customer_aadhaar,
        "customer_pan": customer_pan,
        "customer_address": customer_address,
        "bank_name": bank_name,
        "bank_branch": bank_branch,
        "loan_acc_no": loan_acc_no,
        "pledge_receipt_no": pledge_receipt_no,
        "gross_weight": f"{gross_weight:.2f}",
        "time_limit": time_limit,
        "advance_amount": f"{advance_amount:,}",
        "utr_no": display_utr,
        "cheque_bank": cheque_bank,
        "cheque_no": cheque_no,
        "branch_name": branch_name,
    }

    # Google Sheets Webhook-ல் சேமித்தல்
    try:
      if (
          "google_webhook_url" in st.secrets
          and st.secrets["google_webhook_url"]
      ):
        webhook_url = st.secrets["google_webhook_url"]
        row_data = [
            docket_no,
            txn_date,
            txn_time,
            branch_name,
            customer_name,
            customer_phone,
            customer_aadhaar,
            bank_name,
            loan_acc_no,
            str(gross_weight),
            str(advance_amount),
            utr_no if utr_no.strip() else "Pending",
            cheque_bank,
            cheque_no,
            doc_choice,
        ]
        requests.post(webhook_url, json={"row": row_data}, timeout=10)
        st.toast("✅ Google Sheets-ல் பதிவாகியது!", icon="☁️")
    except Exception:
      pass

    # தேர்ந்தெடுக்கப்பட்ட டெம்ப்ளேட்டைத் தீர்மானித்தல்
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if "குறைந்த தொகை" in doc_choice:
      target_template = "template_simple.html"
    else:
      target_template = "template_dossier.html"

    template_path = os.path.join(current_dir, target_template)

    if not os.path.exists(template_path):
      st.error(f"பிழை: '{target_template}' கோப்பு GitHub-ல் கிடைக்கவில்லை!")
    else:
      try:
        with open(template_path, "r", encoding="utf-8") as f:
          template_str = f.read()

        template = jinja2.Template(template_str)
        rendered_html = template.render(context)

        # PDF உருவாக்கம்
        pdf_bytes = weasyprint.HTML(
            string=rendered_html, base_url=current_dir
        ).write_pdf()
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

        # உலாவி நேரடியாக பிரிண்டரை இயக்கும் ஜாவாஸ்கிரிப்ட்
        print_component = f"""
        <div style="text-align: center; margin-top: 15px;">
            <button id="print_btn" onclick="openAndPrint()" style="
                background-color: #8b0000;
                color: #ffffff;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.15);
                width: 100%;
            ">🖨️ ஆவணத்தை உடனடியாக அச்சிடுக (Click to Print)</button>
        </div>

        <script>
        function openAndPrint() {{
            var byteCharacters = atob("{base64_pdf}");
            var byteNumbers = new Array(byteCharacters.length);
            for (var i = 0; i < byteCharacters.length; i++) {{
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }}
            var byteArray = new Uint8Array(byteNumbers);
            var blob = new Blob([byteArray], {{type: 'application/pdf'}});
            var blobURL = URL.createObjectURL(blob);
            
            var printWin = window.open(blobURL);
            if (printWin) {{
                printWin.focus();
                printWin.onload = function() {{
                    printWin.print();
                }};
            }}
        }}
        // படிவம் சமர்ப்பிக்கப்பட்ட உடன் பிரிண்ட் விண்டோவைத் தானாகத் திறக்க முயற்சிக்கும்
        setTimeout(openAndPrint, 500);
        </script>
        """

        st.success(f"✅ ஆவணக் கோப்பு தயாரானது! கோப்பு எண்: {docket_no}")
        components.html(print_component, height=85)

      except Exception as err:
        st.error(f"ஆவணம் தயாரிப்பதில் பிழை: {err}")
