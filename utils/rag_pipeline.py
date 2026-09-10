import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

def initialize_vector_db(file_path="data/energy_guide_sample.txt", persist_directory="vector_db"):
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_directory)
    return vectorstore

def search_guide_solutions(query: str, k=3):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(persist_directory="vector_db", embedding_function=embeddings)
    results = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
