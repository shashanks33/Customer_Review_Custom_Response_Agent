import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableBranch
from langchain_openai import ChatOpenAI

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

# Initialize the LLM
model = ChatOpenAI(model="gpt-4o-mini")

# Prompt templates
def make_template(feedback_type: str, instructions: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            "You are the Customer Success team at a company. When you reply, speak as the company—"
            "use \"we\" and \"our team\"."
            "straight from the customer’s feedback."
        ),
        (
            "human",
            f"Here’s the customer feedback:\n\n\"{{feedback}}\"\n\nFirst, identify the product or service they mentioned. "
            f"Then draft a full professional email {feedback_type} with subject, greeting, "
            f"{instructions}"
        ),
    ])

positive_feedback_template = make_template(
    "thank-you email",
    "body, and signature"
)
negative_feedback_template = make_template(
    "response",
    "—including an apology for their experience, a proposed solution or next steps, "
    "and a closing/signature."
)
neutral_feedback_template = make_template(
    "request for more details",
    "asking for clarification about that product, and a closing."
)
escalate_feedback_template = make_template(
    "escalation email",
    "noting the need for escalation regarding that product, and a closing/signature."
)

classification_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "Classify the sentiment of this feedback as positive, negative, neutral, or escalate: {feedback}.")
])

# Build the chain
classification_chain = classification_template | model | StrOutputParser()
branches = RunnableBranch(
    (lambda x: "positive" in x.lower(), positive_feedback_template | model | StrOutputParser()),
    (lambda x: "negative" in x.lower(), negative_feedback_template | model | StrOutputParser()),
    (lambda x: "neutral" in x.lower(), neutral_feedback_template | model | StrOutputParser()),
    escalate_feedback_template
)
chain = classification_chain | branches

# Streamlit UI
st.set_page_config(page_title="Customer Review Reply Agent", layout="centered")
st.title("📝 Customer Review Reply Generator")
st.write("Enter a product or service review below, and the agent will draft a custom, company‑branded email reply.")

review_input = st.text_area("Customer Review", height=150)
if st.button("Generate Reply"):
    if not review_input.strip():
        st.error("Please enter the customer's review to generate a reply.")
    else:
        with st.spinner("Generating reply…"):
            try:
                result = chain.invoke({"feedback": review_input})
                st.subheader("Suggested Reply:")
                st.write(result)
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("Powered by Shashank's 3am Coffee and LangChain.")
