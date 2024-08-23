import io
import streamlit as st
import openai
import os
from dotenv import load_dotenv
import fitz  # PyMuPDF

st.cache_data.clear()
load_dotenv()

# Initialize OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")  # Load from environment variable

# Initialize OpenAI Client
client = openai.OpenAI(api_key=api_key)  # Set API key here

# Function to translate text using OpenAI
def translate_text(text, target_language):
    messages = [
        {"role": "system", "content": f"Translate the following text to {target_language}."},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2048,
        temperature=0.7
    )
    translated_text = response.choices[0].message.content.strip()
    return translated_text

# Function to summarize text using OpenAI
def summarize_text(text):
    messages = [
        {"role": "system", "content": "Summarize the following text."},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2048,
        temperature=0.7
    )
    summarized_text = response.choices[0].message.content.strip()
    return summarized_text

# Function to extract text with color from PDF
def extract_text_with_color(pdf_document):
    content = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        color = span.get("color", 0)
                        hex_color = f"#{color:06x}"
                        text = span["text"].strip()
                        if text:
                            content += f"<span style='color:{hex_color};'>{text}</span> "
                    content += "<br>"
            else:
                print(f"Block missing 'lines' key on page {page_num}")
    return content

# Streamlit app setup
st.set_page_config(page_title="Markdown Content Translator", layout="wide")

# Apply custom CSS for text area styling
st.markdown(
    """
    <style>
    .ql-editor {
        border: 2px solid blue;
        padding: 10px;
        resize: both;
        max-height: 500px;
        overflow: auto;
        font-weight: bold;
    }
    .ql-editor.summarized {
        border: 2px solid orange;
    }
    .ql-editor.translated {
        border: 2px solid green;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown("<h1 style='text-align: center;'>Welcome to Markdown Translator</h1>", unsafe_allow_html=True)

# Layout with two equal-width columns
col1, col2 = st.columns([1, 1])

with col1:
    # File upload
    uploaded_file = st.file_uploader("Upload a PDF, TXT, or Markdown file", type=["pdf", "txt", "md"])

    if uploaded_file is not None:
        file_type = uploaded_file.type
        original_content = ""

        if file_type == "application/pdf":
            # Extract text from PDF
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            original_content = extract_text_with_color(pdf_document)
        else:
            # Read text or markdown content
            original_content = uploaded_file.read().decode("utf-8")

        st.markdown("### Original Uploaded Content")
        st.markdown(
            f"""
            <div id="original-editor" class="ql-editor" contenteditable="false">{original_content}</div>
            <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
            <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
            <script>
                var quill = new Quill('#original-editor', {{
                    theme: 'snow',
                    readOnly: true
                }});
            </script>
            """,
            unsafe_allow_html=True
        )

        # Store the original file type in session state
        st.session_state.file_type = file_type

with col2:
    # Translate Options
    st.markdown("### Translate Options")

    target_language = st.selectbox("Select target language for translation", [
        "Hindi", "French", "German", "Chinese", "Japanese", "Korean", "Italian", 
        "Portuguese", "Russian", "Spanish", "Arabic", "Bengali", "Dutch", "Greek", 
        "Hebrew", "Swedish", "Turkish", "Vietnamese", "Polish", "Indonesian"
    ])

    translate_option = st.radio(
        "Choose translation option",
        ("Translate Full Document", "Translate Summarized Content")
    )

    if 'summarized_content' not in st.session_state:
        st.session_state.summarized_content = ""

    # Show Summarize button only if "Translate Summarized Content" is selected
    if translate_option == "Translate Summarized Content":
        if st.button("Summarize") and original_content:
            st.session_state.summarized_content = summarize_text(original_content)
            st.markdown("### Summarized Content")
            st.markdown(
                f"""
                <div id="summarized-editor" class="ql-editor summarized" contenteditable="false">{st.session_state.summarized_content}</div>
                <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
                <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
                <script>
                    var quill = new Quill('#summarized-editor', {{
                        theme: 'snow',
                        readOnly: true
                    }});
                </script>
                """,
                unsafe_allow_html=True
            )

    # Translate summarized content button
    if translate_option == "Translate Summarized Content" and st.session_state.summarized_content and st.button("Translate Summarized Content"):
        translated_summarized_text = translate_summarized_text(st.session_state.summarized_content, target_language)
        st.markdown("### Translated Summarized Content")
        st.markdown(
            f"""
            <div id="translated-editor" class="ql-editor translated" contenteditable="false">{translated_summarized_text}</div>
            <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
            <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
            <script>
                var quill = new Quill('#translated-editor', {{
                    theme: 'snow',
                    readOnly: true
                }});
            </script>
            """,
            unsafe_allow_html=True
        )

        # Download summarized translated content in Markdown format
        st.download_button(
            label="Download Summarized Translated Content (Markdown)",
            data=translated_summarized_text,
            file_name="translated_summarized_content.md",
            mime="text/markdown"
        )

    # Translate full document button
    if translate_option == "Translate Full Document" and st.button("Translate Full Document"):
        if original_content:
            translated_content = translate_text(original_content, target_language)
            st.markdown("### Translated Content")
            st.markdown(
                f"""
                <div id="translated-editor" class="ql-editor translated" contenteditable="false">{translated_content}</div>
                <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
                <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
                <script>
                    var quill = new Quill('#translated-editor', {{
                        theme: 'snow',
                        readOnly: true
                    }});
                </script>
                """,
                unsafe_allow_html=True
            )

            # Download full translated content in Markdown format
            st.download_button(
                label="Download Translated Content (Markdown)",
                data=translated_content,
                file_name="translated_content.md",
                mime="text/markdown"
            )
