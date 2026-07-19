import streamlit as st
import google.generativeai as genai
from PIL import Image
import pytesseract
from docx import Document
from io import BytesIO
import datetime
import os
import platform

# ====== Configure Gemini API Key from Streamlit Secrets ======
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# ====== Configure Tesseract (works on both Windows and Linux Cloud) ======
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# On Linux (Streamlit Cloud), tesseract is installed via packages.txt and found automatically

st.set_page_config(page_title="Medical Summarizer", layout="centered")
st.title("🩺 Medical Text Summarizer & Q&A Generator")

option = st.radio("Choose input method:", ["📝 Paste Text", "🖼️ Upload Image"])

user_text = ""

if option == "📝 Paste Text":
    user_text = st.text_area("Paste your medical text here:", height=200)

else:
    uploaded_file = st.file_uploader("Upload image (JPG, PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", width=300)
        with st.spinner("📖 Extracting English text..."):
            try:
                user_text = pytesseract.image_to_string(image, lang='eng')
            except Exception as e:
                st.error(f"OCR Error: {e}")
                user_text = ""
        if user_text.strip():
            st.success("✅ Text extracted!")
            st.text_area("Extracted text (edit if needed):", user_text, height=150)
        else:
            st.warning("⚠️ No English text found.")

if st.button("🚀 Analyze"):
    if user_text.strip():
        with st.spinner("Processing with AI..."):
            prompt = f"""
            Summarize the following medical text into clear bullet points, 
            then generate 10 Q&As based strictly on the text. 
            Do not omit or add any information. Output in English.
            Text: {user_text}
            """
            response = model.generate_content(prompt)
            result_text = response.text
            st.success("✅ Analysis Done!")
            st.write(result_text)

            # Create Word document
            doc = Document()
            doc.add_heading('Medical Text Analysis Report', 0)
            doc.add_heading('Original Text:', level=1)
            doc.add_paragraph(user_text)
            doc.add_heading('Analysis Result (Summary & Q&A):', level=1)
            for line in result_text.split('\n'):
                if line.strip():
                    doc.add_paragraph(line.strip())
            doc.add_paragraph(f"\nGenerated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)

            st.download_button(
                label="📥 Download as Word Document (.docx)",
                data=doc_io,
                file_name="Medical_Summary.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml"
            )
    else:
        st.warning("Please provide text or image first.")
