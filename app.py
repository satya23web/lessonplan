import streamlit as st
import google.generativeai as genai
import json
import os
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Teacher's Genius Planner", layout="wide")

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
st.title("🍎 Professional Lesson Plan Generator")

# INPUTS
col1, col2, col3 = st.columns(3)
with col1:
    student_name = st.text_input("Teacher Name", "Your Name")
    subject = st.text_input("Subject", "Science")
with col2:
    class_name = st.text_input("Class", "Class 8")
    topic = st.text_input("Topic", "Photosynthesis")
with col3:
    lp_number = st.text_input("Lesson Plan Number", "01")
    period = st.text_input("Period", "40 mins")

col4, col5 = st.columns(2)
with col4:
    tlm = st.text_input("TLM Materials", "Charts, Flashcards")
    # Added UDL Model (Coming Soon) option
    model_type = st.selectbox("Model", ["5E Model", "ICON Model", "UDL Model (Coming Soon)"])
with col5:
    methods = st.text_input("Method", "Constructivist Approach")
    strategies = st.text_input("Strategy", "Collaborative Learning")

st.markdown("---")

# --- CHECK FOR COMING SOON ---
if model_type == "UDL Model (Coming Soon)":
    st.info("🚧 **UDL Model is currently under development.** Please check back later for updates!")
    st.stop()

# --- GENERATE BUTTON ---
if st.button(f"🚀 Generate {subject} Plan #{lp_number}", type="primary"):
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
            
            ### Lesson Plan Identification
            | **Teacher Name** | {student_name} | **Lesson No** | {lp_number} |
            | :--- | :--- | :--- | :--- |
            | **Subject** | {subject} | **Class** | {class_name} |
            | **Topic** | {topic} | **Duration** | {period} |
            | **TLM** | {tlm} | **Model** | 5E Model |
            
            ###**Method:** {methods} 
            ###**Strategy:** {strategies}
            
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
            
            ### Lesson Plan Identification
            | **Teacher Name** | {student_name} | **Lesson No** | {lp_number} |
            | :--- | :--- | :--- | :--- |
            | **Subject** | {subject} | **Class** | {class_name} |
            | **Topic** | {topic} | **Duration** | {period} |
            | **TLM** | {tlm} | **Model** | ICON Model |

            **Method:** {methods} | **Strategy:** {strategies}
            
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
    
    # 1. DISPLAY PLAN (Forcing HTML interpretation for tables)
    # The 'unsafe_allow_html' is critical here to render <br> tags in tables
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
        if st.button("✨ Update Plan"):
            if not refine_instruction:
                st.warning("Please type an instruction.")
            else:
                with st.spinner("Refining..."):
                    refine_prompt = f"""
                    Here is a lesson plan:
                    {st.session_state.generated_plan}
                    
                    USER INSTRUCTION: {refine_instruction}
                    
                    TASK: Rewrite the plan to incorporate the instruction. 
                    Keep the exact same Markdown Table format. Ensure you use `<br>` for line breaks inside the table.
                    """
                    try:
                        new_result = try_generate_content(refine_prompt)
                        st.session_state.generated_plan = new_result
                        st.rerun()
                    except Exception as e:
                        st.error(f"Refinement failed: {e}")

    # --- DONATION CAPTION AT BOTTOM ---
    st.caption("It costs me money to manage it your litttle help will help me a lot to donate click on left donate again")
