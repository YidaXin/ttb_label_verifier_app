## Global imports
from typing import *
import re
import time
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import pandas as pd

## Local imports
from utils import *


#############################
##                         ##
##      Web GUI Setup      ##
##                         ##
#############################

## High contrast, senior-agent friendly styling layout config
st.set_page_config(
    page_title="TTB Local AI Label Verifier (Air-Gapped)",
    layout="wide",
    initial_sidebar_state="expanded"
)

## Custom High Contrast / Large CSS injection for Dave & senior agents
st.markdown("""
<style>
    .big-font { font-size: 20px !important; font-weight: 500; }
    .compliance-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .pass-bg { background-color: #d4edda; color: #155724; border-left: 6px solid #28a745; }
    .fail-bg { background-color: #f8d7da; color: #721c24; border-left: 6px solid #dc3545; }
    .stButton>button { width: 100%; height: 50px; font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

#############################
##  Right Hand Side Panel  ##
#############################

st.title("📋 AI-Powered Alcohol Label Verification")
st.subheader("Prototype Digital Compliance Portal | 🔒 Local Air-Gapped Mode Active")
st.write("---")

# ## File upload handler, supports batch drag-and-drop
# uploaded_files: List[UploadedFile] | None = st.file_uploader(
#     "Drag & Drop Label Artwork Files Here (Supports Single or Batch Processing)",
#     type=["png", "jpg", "jpeg"],
#     accept_multiple_files=True
# )

##########################
##  Left Hand Side Bar  ##
##########################

st.sidebar.header("⚙️ Core Controls")

if "model_preloaded" not in st.session_state:
    st.session_state.model_preloaded = False

if not st.session_state.model_preloaded:
    if st.sidebar.button("🚀 Pre-Load AI Model into RAM/VRAM", type="primary"):
        with st.spinner("Waking up local LLM weights..."):
            ## Change "qwen2.5vl" if you switch models later
            success: bool = load_local_llm("qwen2.5:1.5b")
            if success:
                st.session_state.model_preloaded = True
                st.sidebar.success("✅ Model Warm & Ready!")
                st.rerun()
            else:
                st.sidebar.error("❌ Failed to connect to Ollama.")
else:
    st.sidebar.success("🔥 AI Model Pre-Loaded & Active")
    if st.sidebar.button("🔄 Reset / Clear Model Cache"):
        st.session_state.model_preloaded = False
        st.rerun()

st.sidebar.write("---")

batch_processing_mode: bool = st.sidebar.checkbox("Activate Batch Processing Mode (Multiple Product Applications)", value=False)

st.sidebar.write("---")

st.sidebar.header("🔍 Form Cross-Reference Data")
st.sidebar.write("Input the official COLA application record details to verify against the label artwork.")

form_brand_name = st.sidebar.text_input("Application Brand Name", "")
form_class_type = st.sidebar.text_input("Application Class/Type", "")
form_abv_content = st.sidebar.text_input("Application ABV", "")
form_net_contents = st.sidebar.text_input("Application Net Contents", "")
# form_producer_details = st.sidebar.text_input("Application Producer Details", "")
# form_allergens_and_additives = st.sidebar.text_input("Application Allergens & Addtives", "")
# form_distilled_spirits_details = st.sidebar.text_input("Application Distilled Spirits Details", "")
# form_wine_details = st.sidebar.text_input("Application Wine Details", "")
# form_serving_facts = st.sidebar.text_input("Application Serving Facts", "")

# st.sidebar.info("💡 **Tip:** Drop multiple images below to activate Batch Mode processing for large importer manifests.")

st.sidebar.info("💡 **Tip:** To process an explicit batch manifest containing multiple different product applications, "
                "click the checkbox below to decouple inputs.")




#######################
##                   ##
##      Helpers      ##
##                   ##
#######################

def run_verification(file_obj):
    """ Call analyze_image_label to run verification. """
    start_time = time.time()
    file_obj.seek(0)  # force rewind
    img_bytes = file_obj.read()
    # extracted_data = analyze_label_image(img_bytes)
    extracted_data = run_pipeline(img_bytes)
    elapsed = time.time() - start_time
    return extracted_data, elapsed, img_bytes

# def check_fuzzy_match(form_val, label_val) -> bool:
#     """ Fuzzy-match helper """
#     if not label_val or not form_val:
#         return False
#     return (form_val.strip().lower() in label_val.strip().lower() 
#             or label_val.strip().lower() in form_val.strip().lower())

def check_fuzzy_match(form_val, label_val) -> bool:
    """ Fuzzy-match helper that normalizes punctuation and whitespace """
    def _normalize(text: str) -> str:
        # Convert to lowercase and strip leading/trailing spaces
        text = text.strip().lower()
        # Remove periods (handles fl. oz. -> fl oz)
        text = text.replace(".", "")
        # Replace multiple spaces/newlines with a single space
        text = re.sub(r'\s+', ' ', text)
        return text
    if not label_val or not form_val:
        return False
    clean_form = _normalize(form_val)
    clean_label = _normalize(label_val)
    return clean_form in clean_label or clean_label in clean_form


####################
##                ##
##      MAIN      ##
##                ##
####################

if __name__ == "__main__":
    ## File upload handler, supports batch drag-and-drop
    uploaded_files: List[UploadedFile] | None = st.file_uploader(
        "Drag & Drop Label Artwork Files Here (Supports Single or Batch Processing)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    if not uploaded_files:
        st.info("👋 Welcome! Please drag and drop or upload one or more label images above to begin the compliance audit.")
    else:
        num_files: int = len(uploaded_files)
        #############################################################
        ##  Single Application: Handles 1 or more images per COLA  ##
        #############################################################
        if not batch_processing_mode:
            st.subheader(f"📸 Single Processing Mode Activated: 1 Product Application with {num_files} inputs")
            with st.spinner("Local AI analyzing label compliance fields..."):
                try:
                    data_brand_name: str = ""
                    data_class_type: str = ""
                    data_abv_content: str = ""
                    data_net_contents: str = ""
                    # data_producer_details: str = "N/A"
                    # data_spirits: str = "N/A"
                    # data_wine: str = "N/A"
                    # data_serving: str = "None"
                    allergens = set()
                    final_govt_warning = None
                    total_speed = 0.0
                    file_previews = []
                    for file in uploaded_files:
                        data, speed, raw_bytes = run_verification(file)
                        total_speed += speed
                        file_previews.append((raw_bytes, file.name))
                        ## Synthesize text fields by selecting non-null values extracted across panels
                        if data.brand_name:
                            data_brand_name = data.brand_name
                        if data.class_type:
                            data_class_type = data.class_type
                        if data.abv_content:
                            data_abv_content = data.abv_content
                        if data.net_contents:
                            data_net_contents = data.net_contents
                        # if data.producer_details and data.producer_details.name_and_address:
                        #     data_producer_details = data.producer_details.name_and_address
                        # if data.distilled_spirits_details:
                        #     data_spirits = f"Proof: {data.distilled_spirits_details.alcohol_proof} | {data.distilled_spirits_details.statement_of_composition}"
                        # if data.wine_details:
                        #     data_wine = f"Origin: {data.wine_details.appellation_of_origin} | {data.wine_details.varietal_designation}"
                        # if data.serving_facts and data.serving_facts.has_serving_facts:
                        #     data_serving = data.serving_facts.raw_panel_text
                        # if data.allergens_and_additives:
                        #     if data.allergens_and_additives.contains_sulfites == 1:
                        #         allergens.add("Contains Sulfites")
                        #     if data.allergens_and_additives.contains_yellow_five == 1:
                        #         allergens.add("Contains Yellow 5")
                        #     if data.allergens_and_additives.contains_cochineal_carmine == 1:
                        #         allergens.add("Contains Carmine")
                        #     if data.allergens_and_additives.contains_aspartame == 1:
                        #         allergens.add("Contains Aspartame")
                        ## GOVERNMENT WARNING extraction (Prioritize the panel containing the health statement)
                        if data.government_warning and data.government_warning.has_warning == 1:
                            if not final_govt_warning or data.government_warning.is_header_all_caps == 1:
                                final_govt_warning = data.government_warning
                    ## If no loaded image contains GOVERNMENT WARNING, assign the last scanned structure
                    if not final_govt_warning:
                        final_govt_warning = data.government_warning
                    ## Latency constraint message checking
                    if total_speed <= 5.0:
                        st.success(f"⏱️ Total Application Processing Time: **{total_speed:.2f}s** (Under Sarah's 5s threshold target!)")
                    else:
                        st.warning(f"⏱️ Total Application Processing Time: **{total_speed:.2f}s** (Local multi-panel sequence execution overhead)")
                    # Layout presentation splits
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        for raw_bytes, filename in file_previews:
                            # st.image(raw_bytes, caption=filename, use_container_width=True)
                            st.image(raw_bytes, caption=filename, use_column_width=True)
                    with col2:
                        st.markdown("### 🧬 Automated Cross-Reference Verification Checklist")
                        st.write("The AI cross-checked all uploaded design layers against your Form Application input fields:")
                        data_allergens = ", ".join(allergens) if allergens else "None Detected"
                        fields = [
                            ("Brand Name", form_brand_name, data_brand_name),
                            ("Class/Type", form_class_type, data_class_type),
                            ("ABV Content", form_abv_content, data_abv_content),
                            ("Net Contents", form_net_contents, data_net_contents),
                            # ("Producer Details", form_producer_details, data_producer_details),
                            # ("Allergens & Additives", form_allergens_and_additives, data_allergens),
                            # ("Distilled Spirits Details", form_distilled_spirits_details, data_spirits),
                            # ("Wine Details", form_wine_details, data_wine),
                            # ("Serving Facts", form_serving_facts, data_serving)
                        ]
                        for name, form_value, label_value in fields:
                            is_ok = check_fuzzy_match(form_value, label_value)
                            bg_class = "pass-bg" if is_ok else "fail-bg"
                            icon = "✅ MATCH" if is_ok else "❌ MISMATCH / REVIEW REQUIRED"
                            st.markdown(f"""
                            <div class="compliance-card {bg_class}">
                                <strong>{name}:</strong><br>
                                • Form Input: <code>{form_value}</code><br>
                                • Extracted from Label artwork: <code>{label_value}</code><br>
                                <strong>Status: {icon}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        ## Mandatory check for GOVERNMENT WARNING (a.k.a., Jenny's Strict Rules)
                        st.markdown("### ⚠️ Mandatory GOVERNMENT WARNING Diagnostics")
                        w = final_govt_warning
                        if not w or w.has_warning == 0:
                            st.markdown(
                                '<div class="compliance-card fail-bg"><strong>❌ CRITICAL REJECTION:</strong> No GOVERNMENT WARNING statement detected across any of the submitted label panels.</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            g1 = "✅ Yes" if w.is_header_all_caps == 1 else "❌ No (Rejection Trigger: Must be ALL CAPS)"
                            g2 = "✅ Yes" if w.is_header_bold == 1 else "❌ No (Rejection Trigger: Must be BOLDED)"
                            g3 = "✅ Yes" if w.matches_standard_wording == 1 else "⚠️ Review Required (Minor phrasing deviations caught)"
                            warning_all_passed: bool = w.is_header_all_caps == 1 and w.is_header_bold == 1 and w.matches_standard_wording == 1
                            final_warning_bg = "pass-bg" if warning_all_passed else "fail-bg"
                            st.markdown(f"""
                            <div class="compliance-card {final_warning_bg}">
                                <strong>Extracted Warning Text:</strong> <pre style='white-space: pre-wrap;'>"{w.exact_text_extracted}"</pre>
                                • Is "GOVERNMENT WARNING:" in ALL CAPS?: <b>{g1}</b><br>
                                • Is header bolded?: <b>{g2}</b><br>
                                • Word-for-word legal wording matches?: <b>{g3}</b>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Failed to process verification run natively: {e}")

        ##########################################################################################
        ##  Multiple labels: use batch-processing, per Janet's request from the Seattle Office  ##
        ##########################################################################################
        else:
            st.subheader(f"📦 Batch Processing Mode Activated: {num_files} Product Applications Queued")
            st.info("Processing complete manifest stream natively below. Rejections flag dynamically for manual routing.")
            run_batch = st.button("⚡ Execute Batch Audit Manifest")
            if run_batch:
                progress_bar = st.progress(0)
                results = []
                for idx, file in enumerate(uploaded_files):
                    st.write(f"Auditing file {idx + 1}/{num_files}: **{file.name}**...")
                    try:
                        ## For batch processing, we're no longer trying to examine every image;
                        ## instead, we're just trying to get the final result in a table format,
                        ## as quickly as possible.
                        data, speed, _ = run_verification(file)
                        warning_ok: bool = (data.government_warning.has_warning == 1
                                            and data.government_warning.is_header_all_caps == 1 
                                            and data.government_warning.is_header_bold == 1)
                        status = "✅ PASS" if warning_ok else "🚨 REJECT / AUDIT"
                        # data_producer: str = data.producer_details.name_and_address if data.producer_details else "N/A"
                        # allergens: List[str] = []
                        # if data.allergens_and_additives:
                        #     if data.allergens_and_additives.contains_sulfites == 1:
                        #         allergens.append("Contains Sulfites")
                        #     if data.allergens_and_additives.contains_yellow_five == 1:
                        #         allergens.append("Contains Yellow 5")
                        #     if data.allergens_and_additives.contains_cochineal_carmine == 1:
                        #         allergens.append("Contains Carmine")
                        #     if data.allergens_and_additives.contains_aspartame == 1:
                        #         allergens.append("Contains Aspartame")
                        # data_allergens: str = ", ".join(allergens) if allergens else "None Detected"
                        # data_spirits: str = \
                        #     f"Proof: {data.distilled_spirits_details.alcohol_proof} " \
                        #         if data.distilled_spirits_details else "N/A"
                        # data_wine: str = \
                        #     f"Origin: {data.wine_details.appellation_of_origin} " \
                        #         if data.wine_details else "N/A"
                        # data_serving: str = \
                        #     data.serving_facts.raw_panel_text \
                        #         if (data.serving_facts and data.serving_facts.has_serving_facts) else "None"
                        results.append({
                            "File Name": file.name,
                            "Warning Valid?": "Valid" if warning_ok else "Invalid Format",
                            "Brand Name Found": data.brand_name,
                            "Class/Type Found": data.class_type,
                            "ABV Content Found": data.abv_content,
                            "Net Contents Found": data.net_contents,
                            # "Producer Details Found": data_producer,
                            # "Allergens & Additives Found": data_allergens,
                            # "Distilled Spirits Details Found": data_spirits,
                            # "Wine Details Found": data_wine,
                            # "Serving Facts Found": data_serving,
                            "Audit Latency": f"{speed:.2f}s",
                            "Decision Matrix Status": status
                        })
                    except Exception:
                        results.append({
                            "File Name": file.name,
                            "Warning Valid?": "ERR",
                            "Brand Found": "ERR", 
                            "Class/Type Found": "ERR",
                            "ABV Found": "ERR",
                            "Net Contents Found": "ERR",
                            # "Producer Details Found": "ERR",
                            # "Allergens & Additives Found": "ERR",
                            # "Distilled Spirits Details Found": "ERR",
                            # "Wine Details Found": "ERR",
                            # "Serving Facts Found": "ERR",
                            "Audit Latency": "ERR",
                            "Decision Matrix Status": "🚨 CRASH / FAILED READ"
                        })
                    progress_bar.progress((idx + 1) / num_files)
                st.success("🎉 Batch processing routine cleared completely.")
                results = pd.DataFrame(results).astype(str)
                st.table(results)
