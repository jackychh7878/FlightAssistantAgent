import re
import os
from dotenv import load_dotenv
import requests
import numpy as np
import openai
from langchain_core.tools import tool
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma


load_dotenv()

# Define the directory where you want to save the file
SAVE_DIR = "./src/rag_doc"
FILE_NAME = "swiss_faq.md"
PERSIST_DIR = "./src/vector_db"
embedding = AzureOpenAIEmbeddings(model="text-embedding-3-small")


def download_rag_doc():
    # Combine the directory and file name to get the full path
    DOC_PATH = os.path.join(SAVE_DIR, FILE_NAME)
    if not os.path.exists(DOC_PATH):
        # Create the directory if it doesn't exist
        os.makedirs(SAVE_DIR, exist_ok=True)

        response = requests.get(
            "https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md"
        )
        response.raise_for_status()

        faq_text = response.text
        with open(DOC_PATH, "w", encoding="utf-8") as f:
            f.write(faq_text)
    else:
        print("RAG doc already exists locally.")

    # Check if the database already exists
    if not os.path.exists(PERSIST_DIR):
        # Load and embed the doc list to vector db
        # loader = DirectoryLoader(SAVE_DIR, glob="**/*.md", loader_cls=TextLoader,
        #                          loader_kwargs={"autodetect_encoding": True}, use_multithreading=True,
        #                          show_progress=True)
        # docs = loader.load()
        # print(docs[0].page_content[:100])
        raw_documents = TextLoader(DOC_PATH, autodetect_encoding=True).load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        documents = text_splitter.split_documents(raw_documents)

        os.makedirs(PERSIST_DIR, exist_ok=True)

        # Persist the Database
        Chroma.from_documents(documents=documents, embedding=embedding, persist_directory=PERSIST_DIR)
        print("Vector database created and persisted.")
    else:
        print("Vector database already exists.")

# download_rag_doc()
# print(docs[0].page_content[:100])
#
# class VectorStoreRetriever:
#     def __init__(self):
#         self.index = None

## https://github.com/hwchase17/chroma-langchain/blob/master/persistent-qa.ipynb

# Test Run
vectordb = Chroma(persist_directory="./src/vector_db", embedding_function=embedding)
query = "Refund Policy for the flight ticket"
# docs = vectordb.similarity_search(query=query, k=4)

@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted.
    Use this before making any flight changes performing other 'write' events."""
    docs = vectordb.similarity_search(query, k=4)
    return "\n\n".join([doc.page_content for doc in docs])
