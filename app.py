import streamlit as st
import pandas as pd
from docx import Document
import spacy
import subprocess
import sys

# โหลดโมเดลภาษาอังกฤษของ spaCy (โหลดแค่ครั้งเดียว)
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # ถ้ายังไม่มีโมเดล ให้สั่งดาวน์โหลดอัตโนมัติ
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        return spacy.load("en_core_web_sm")

st.title("🕵️‍♂️ NER Glossary Extractor")
st.write("อัปเกรดใหม่: ระบบสกัดชื่อเฉพาะ (ชื่อคน, สถานที่, องค์กร) ออกจากเอกสารอัตโนมัติ ช่วยนักแปลสร้าง Termbase ได้ในคลิกเดียว!")

# โหลด AI Model
with st.spinner('กำลังเตรียมระบบ AI...'):
    nlp = load_spacy_model()

uploaded_file = st.file_uploader("อัปโหลดเอกสารภาษาอังกฤษ (.txt หรือ .docx)", type=["txt", "docx"])

if uploaded_file is not None:
    text = ""
    if uploaded_file.name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8")
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])

    if text:
        st.info("🤖 AI กำลังสกัดชื่อเฉพาะให้คุณ...")
        
        # ประมวลผลด้วย spaCy
        doc_spacy = nlp(text)
        
        # ดึงข้อมูล Entity
        entities = []
        for ent in doc_spacy.ents:
            # กรองเอาเฉพาะที่เกี่ยวกับงานแปลบ่อยๆ (คน, สถานที่, องค์กร)
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:
                label_th = ""
                if ent.label_ == "PERSON": label_th = "ชื่อคน (Person)"
                elif ent.label_ == "ORG": label_th = "องค์กร (Organization)"
                elif ent.label_ in ["GPE", "LOC"]: label_th = "สถานที่ (Location)"
                
                entities.append({"คำศัพท์ต้นฉบับ (Source)": ent.text.strip(), "ประเภท (Entity Type)": label_th})
        
        if entities:
            # สร้างตารางและนับความถี่ (จัดกลุ่มคำที่ซ้ำกัน)
            df = pd.DataFrame(entities)
            df_counts = df.groupby(["คำศัพท์ต้นฉบับ (Source)", "ประเภท (Entity Type)"]).size().reset_index(name='เจอในเอกสาร (ครั้ง)')
            df_counts = df_counts.sort_values(by="เจอในเอกสาร (ครั้ง)", ascending=False)

            st.success("✅ สกัดข้อมูลสำเร็จ! นำไปใช้ทำ Glossary ได้เลย")
            st.dataframe(df_counts, use_container_width=True)

            # ปุ่มดาวน์โหลด CSV
            csv = df_counts.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ดาวน์โหลด Glossary (CSV)",
                data=csv,
                file_name='ner_extracted_glossary.csv',
                mime='text/csv'
            )
        else:
            st.warning("ไม่พบชื่อเฉพาะ (คน, องค์กร, สถานที่) ในเอกสารนี้ครับ")
