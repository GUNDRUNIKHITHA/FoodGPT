import json
from fpdf import FPDF
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import VectorDBQA,RetrievalQA, LLMChain
from langchain.retrievers import MultiQueryRetriever
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
import sys

class SwiggyDataRetriever:
    def __init__(self, json_file, google_api_key, embedding_model='models/embedding-001', chat_model_name='gemini-1.5-pro'):
        self.json_file = json_file
        self.google_api_key = google_api_key
        self.embedding_model = embedding_model
        self.chat_model_name = chat_model_name
        self.pdf_file = "swiggy_data.pdf"
        self.texts = []
        self.vectordb = None
        self.qa_chain = None
        
    def load_json(self):
        with open(self.json_file, 'r') as file:
            return json.load(file)

    def generate_pdf(self, data):
        text_content = ""
        for item in data:
            text_content += f"Dish: {item['Dish Name']}\n"
            text_content += f"Category: {item['Category']}\n"
            text_content += f"Price (INR): {item['Price (INR)']}\n"
            text_content += f"Rating: {item['Rating']}\n"
            text_content += f"Restaurant: {item['Restaurant Name']}\n"
            text_content += f"Address: {item['Address']}\n"
            text_content += f"Delivery Time: {item['Delivery Time']} mins\n\n"
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, text_content)
        pdf.output(self.pdf_file)

    def process_pdf(self):
        loader = PyPDFLoader(self.pdf_file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.texts = text_splitter.split_documents(documents)

    def setup_embeddings(self):
        embeddings = GoogleGenerativeAIEmbeddings(
            model=self.embedding_model,
            google_api_key=self.google_api_key,
            task_type="retrieval_query"
        )
        return embeddings

    def setup_chat_model(self):
        safety_settings = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
        chat_model = ChatGoogleGenerativeAI(
            model=self.chat_model_name,
            google_api_key=self.google_api_key,
            temperature=0.3,
            safety_settings=safety_settings
        )
        return chat_model

    def setup_vector_store(self, embeddings):
        self.vectordb = Chroma.from_documents(documents=self.texts, embedding=embeddings)

    def setup_qa_chain(self, chat_model):
        prompt_template = """
        Context: \n {context}
        Question: \n {question}
        Answer:
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=['context', 'question'])
        retriever_from_llm = MultiQueryRetriever.from_llm(retriever=self.vectordb.as_retriever(search_kwargs={"k": 5}), llm=chat_model)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=chat_model,
            retriever=retriever_from_llm,
            return_source_documents=True,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt}
        )

    def run_query(self, query):
        if not self.qa_chain:
            raise Exception("QA chain is not initialized. Run setup first.")
        response = self.qa_chain.invoke({"query": query})
        return response['result']

    def setup(self):
        data = self.load_json()
        self.generate_pdf(data)
        self.process_pdf()
        embeddings = self.setup_embeddings()
        chat_model = self.setup_chat_model()
        self.setup_vector_store(embeddings)
        self.setup_qa_chain(chat_model)

# if __name__ == "__main__":
    # google_api_key = "AIzaSyA75km2BQruVC49MdyXCsx4lMshFoginNo"  # Replace with your API key
    # json_file = "swiggy_results.json"
    # retriever = SwiggyDataRetriever(json_file, google_api_key)
    # retriever.setup()
    # user_query = "Sri Manikanta Restaurant"
    # result = retriever.run_query(user_query)
    # print(result)
