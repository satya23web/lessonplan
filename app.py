import streamlit as st
import google.generativeai as genai
import json
import os
import datetime

# --- CONFIGURATION (Mobile Friendly) ---
# Changed layout to 'centered' for a better mobile app experience
st.set_page_config(page_title="Teacher's Genius Planner", layout="centered")

# 🔴 SECRETS API KEY (For Streamlit Cloud)
if "GOOGLE_API_KEY" in st.secrets:
    HIDDEN_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("❌ API Key missing in Secrets. Please add GOOGLE_API_KEY in Streamlit Settings.")
    st.stop()

# --- DATABASE ---
DB_FILE = "lesson_history.json"

def load_history():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_to_history(plan_data):
    history = load_history()
    plan_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Unique ID
    history.insert(0, plan_data) 
    with open(DB_FILE, "w") as f:
        json.dump(history, f, indent=4)

def delete_plan(timestamp):
    """Deletes a plan based on its unique timestamp"""
    history = load_history()
    new_history = [item for item in history if item.get("timestamp") != timestamp]
    with open(DB_FILE, "w") as f:
        json.dump(new_history, f, indent=4)

# --- MODEL FUNCTION ---
def try_generate_content(prompt):
    if not HIDDEN_API_KEY:
        raise Exception("API Key is missing!")
        
    genai.configure(api_key=HIDDEN_API_KEY)
    model_list = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro"]
    
    last_error = ""
    for model_name in model_list:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = str(e)
            continue
    raise Exception(f"Connection failed. Error: {last_error}")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    if HIDDEN_API_KEY:
        st.success("✅ API System: Active")
    
    st.markdown("---")

    # 💾 BACKUP BUTTON
    st.subheader("💾 Backup Data")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            st.download_button(
                label="📥 Download History File",
                data=f,
                file_name="lesson_history.json",
                mime="application/json",
                help="Download this file and upload it to GitHub to save your history permanently."
            )
    else:
        st.caption("No history to backup yet.")

    st.markdown("---")
    
    # ❤️ DONATION SECTION
    with st.expander("❤️ Support the Developer", expanded=True):
        st.markdown("If it truly saved your time feel free to donate.")
        
        # 1. Buy Me A Coffee Button
        st.markdown(
            """
            <a href="https://www.buymeacoffee.com/scarlet25" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 200px !important;" >
            </a>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # 2. UPI Copy Option
        st.write("**Or via UPI:**")
        st.code("kumarsatya75045-3@okhdfcbank", language="text")
        
        if st.button("I sent a donation! 🎉"):
            st.balloons()
            st.success("You are amazing! Thank you!")

    st.markdown("---")
    
    # 📜 HISTORY (With Delete)
    st.header("📚 History")
    history = load_history()
    if not history:
        st.info("No plans yet.")
    else:
        for item in history:
            label = f"{item['subject']} - LP #{item['lp_number']}"
            
            with st.expander(label):
                st.caption(f"Topic: {item['topic']}")
                
                col_h1, col_h2 = st.columns([1, 1])
                
                # Load Button
                with col_h1:
                    if st.button("📂 Load", key=f"load_{item['timestamp']}"):
                        st.session_state.generated_plan = item['content']
                        st.rerun()
                
                # Delete Button
                with col_h2:
                    if st.button("🗑️ Delete", key=f"del_{item['timestamp']}"):
                        delete_plan(item['timestamp'])
                        st.rerun()

# --- MAIN APP ---
st.title("🍎 Teacher's Genius Planner")
st.markdown("Create professional lesson plans in seconds.")

# --- MOBILE FRIENDLY INPUTS ---
# Main Topic Input (Full Width)
topic = st.text_input("📌 Topic", "Photosynthesis", help="What are you teaching today?")

# 2-Column Layout for Essentials
col1, col2 = st.columns(2)

with col1:
    subject = st.text_input("Subject", "Science")
    class_name = st.text_input("Class", "Class 8")
    model_type = st.selectbox("Model", ["5E Model", "ICON Model", "UDL Model (Coming Soon)"])

with col2:
    student_name = st.text_input("Teacher Name", "Your Name")
    lp_number = st.text_input("Lesson Plan No.", "01")
    period = st.text_input("Period Duration", "40 mins")

# Expander for Advanced details (Keeps mobile view clean)
with st.expander("🛠️ Advanced Settings (Methods & Materials)", expanded=False):
    tlm = st.text_input("TLM Materials", "Charts, Flashcards")
    methods = st.text_input("Method", "Constructivist Approach")
    strategies = st.text_input("Strategy", "Collaborative Learning")

st.markdown("---")

# --- CHECK FOR COMING SOON ---
if model_type == "UDL Model (Coming Soon)":
    st.info("🚧 **UDL Model is currently under development.** Please check back later for updates!")
    st.stop()

# 🔗 YOUR REFERRAL LINK
navi_link = "https://r.navi.com/ft4geB" 

# --- GENERATE BUTTON ---
# Using full column width for button on mobile
if st.button(f"🚀 Generate Lesson Plan", type="primary", use_container_width=True):
    with st.spinner("Writing detailed plan..."):
        
        # --- PROMPTS ---
        if model_type == "5E Model":
            prompt = f"""
            Act as an expert student teacher. Create a 5E Lesson Plan.
            
            **CONTEXT:**
            Teacher: {student_name}, Lesson Plan No: {lp_number}
            Subject: {subject}, Topic: {topic}, Class: {class_name}
            Method: {methods}, Strategy: {strategies}, TLM: {tlm}
            
            **INSTRUCTIONS:**
            1. Write in FIRST PERSON ("I will...").
            2. Use a CLEAN MARKDOWN TABLE for phases.
            3. **CRITICAL:** Do NOT use standard newlines (\\n) inside the table cells. Use HTML `<br>` tags for line breaks inside the table cells so the table stays perfect.
            4. "Evaluate" phase must have 3 numbered questions.
            
            **OUTPUT FORMAT:**
            
            **Lesson Plan Identification**
            | | | | |
            | :--- | :--- | :--- | :--- |
            | **Teacher** | {student_name} | **Lesson No** | {lp_number} |
            | **Subject** | {subject} | **Class** | {class_name} |
            | **Topic** | {topic} | **Duration** | {period} |
            | **TLM** | {tlm} | **Model** | 5E Model |
            
            **Method:** {methods} | **Strategy:** {strategies}

            ---
            **🎁 Special Offer for Teachers**
            Get **tons of cashback** directly to your bank account! Download the **Navi App** using the link below:
            👉 [**Click Here to Download Navi & Claim Cashback**]({navi_link})
            *(Safe, secure UPI app trusted by millions)*
            ---
            
            ### Objectives:
            [List Objectives]
            
            ### 5E Process:
            | Phase | Activity (Teacher & Student) | Learning Outcome |
            | :--- | :--- | :--- |
            | **Engage** | [Detail] | [Outcome] |
            | **Explore** | [Detail] | [Outcome] |
            | **Explain** | [Detail] | [Outcome] |
            | **Elaborate** | [Detail] | [Outcome] |
            | **Evaluate** | [Detail] | [Outcome] |

            ---
            *It costs me money to manage it your litttle help will help me a lot to donate click on left top button to donate*
            """
        elif model_type == "ICON Model":
            prompt = f"""
            Act as an expert student teacher. Create an ICON Model Lesson Plan based on the EXACT steps below.
            
            **CONTEXT:**
            Teacher: {student_name}, LP #{lp_number}, Subject: {subject}, Topic: {topic}.
            Class: {class_name}, Period: {period}, TLM: {tlm}.
            Method: {methods}, Strategy: {strategies}.
            
            **INSTRUCTIONS:**
            1. Use a MARKDOWN TABLE with 2 columns: "ICON Phase & Activity" on the left, "Learning Outcome" on the right.
            2. **CRITICAL:** Use HTML `<br>` tags for line breaks inside table cells. Do NOT use normal newlines inside the table.
            3. Follow these exact 8 phases.

            **OUTPUT FORMAT:**
            
            **Lesson Plan Identification**
            | | | | |
            | :--- | :--- | :--- | :--- |
            | **Teacher** | {student_name} | **Lesson No** | {lp_number} |
            | **Subject** | {subject} | **Class** | {class_name} |
            | **Topic** | {topic} | **Duration** | {period} |
            | **TLM** | {tlm} | **Model** | ICON Model |

            **Method:** {methods} | **Strategy:** {strategies}
            
            ---
            **🎁 Special Offer for Teachers**
            Get **tons of cashback** directly to your bank account! Download the **Navi App** using the link below:
            👉 [**Click Here to Download Navi & Claim Cashback**]({navi_link})
            *(Safe, secure UPI app trusted by millions)*
            ---
            
            ### Outcomes:
            [List Outcomes]
            
            ### ICON Process:
            | ICON Phase & Activity | Learning Outcome |
            | :--- | :--- |
            | **1. Authentic Observation**<br>[Teacher divides class into two groups... details based on {topic}] | [Specific Outcome] |
            | **2. Interpretation Construction**<br>[Teacher assigns activity based on results... details] | [Specific Outcome] |
            | **3. Contextualization**<br>[Students relate observation to text... Teacher guides... details] | [Specific Outcome] |
            | **4. Cognitive Apprenticeship**<br>[Teacher guides students to alter observation... Students re-analyze... Teacher asks real-life scenario questions] | [Specific Outcome] |
            | **5. Collaboration**<br>[Teacher divides class into two groups... provides apparatus... details] | [Specific Outcome] |
            | **6. Multiple Interpretation**<br>[Teacher asks questions to groups performing activity... details] | [Specific Outcome] |
            | **7. Multiple Manifestation**<br>[Students summarize interpretations... Teacher assists... details] | [Specific Outcome] |
            | **8. Application**<br>[Teacher gives specific questions to solve... details] | [Specific Outcome] |

            ---
            *It costs me money to manage it your litttle help will help me a lot to donate click on left top button to donate*
            """
        
        try:
            result = try_generate_content(prompt)
            st.session_state.generated_plan = result
            
            # Auto-Save to History
            save_to_history({
                "lp_number": lp_number,
                "topic": topic,
                "subject": subject,
                "date": datetime.datetime.now().strftime("%d-%m-%Y"),
                "content": result
            })
        except Exception as e:
            st.error(f"Error: {e}")

# --- DISPLAY & CUSTOMIZATION ---
if "generated_plan" in st.session_state:
    st.markdown("---")
    st.success("✅ Plan Generated Successfully!")
    
    # 1. DISPLAY PLAN
    st.markdown(st.session_state.generated_plan, unsafe_allow_html=True)
    
    # 2. CUSTOMIZATION TOOL
    st.markdown("---")
    st.header("🛠️ Modify this Plan")
    
    col_ref1, col_ref2 = st.columns([4, 1])
    with col_ref1:
        refine_instruction = st.text_input("Instruction", placeholder="e.g., Change the Explore activity to use a YouTube video instead.")
    with col_ref2:
        st.write("") 
        st.write("") 
        if st.button("✨ Update Plan", use_container_width=True):
            if not refine_instruction:
                st.warning("Please type an instruction.")
            else:
                with st.spinner("Refining..."):
                    # UPDATED ROBUST REFINEMENT PROMPT
                    refine_prompt = f"""
                    Act as an expert teacher. Update the lesson plan below based on the user's request.
                    
                    **CURRENT PLAN:**
                    {st.session_state.generated_plan}
                    
                    **USER REQUEST:** {refine_instruction}
                    
                    **STRICT OUTPUT FORMAT (YOU MUST FOLLOW THIS EXACTLY):**
                    
                    1. **TOP SECTION (Identification Table):**
                       **Lesson Plan Identification**
                       | | | | |
                       | :--- | :--- | :--- | :--- |
                       | **Teacher** | {student_name} | **Lesson No** | {lp_number} |
                       | **Subject** | {subject} | **Class** | {class_name} |
                       | **Topic** | {topic} | **Duration** | {period} |
                       | **TLM** | {tlm} | **Model** | {model_type} |
                       
                       **Method:** {methods} | **Strategy:** {strategies}
                    
                    2. **REFERRAL SECTION (Keep exactly this format):**
                       ---
                       **🎁 Special Offer for Teachers**
                       Get **tons of cashback** directly to your bank account! Download the **Navi App** using the link below:
                       👉 [**Click Here to Download Navi & Claim Cashback**]({navi_link})
                       *(Safe, secure UPI app trusted by millions)*
                       ---
                    
                    3. **CONTENT SECTION:**
                       - Rewrite the Objectives and Phases based on the User Request.
                       - Use a clean MARKDOWN TABLE for the phases (Engage, Explore, etc.).
                       - Use HTML `<br>` for line breaks inside the table.
                       
                    **GENERATE THE FULL PLAN:**
                    """
                    try:
                        new_result = try_generate_content(refine_prompt)
                        st.session_state.generated_plan = new_result
                        st.rerun()
                    except Exception as e:
                        st.error(f"Refinement failed: {e}")

    
