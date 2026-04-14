"""
API client for the RAG Pipeline backend. All functions communicate with
the FastAPI backend over HTTP. The backend URL is read from API_BASE_URL.
"""

import os
import requests
import streamlit as st
from typing import List, Dict, Any, Optional

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = 60
UPLOAD_TIMEOUT_SECONDS = 300

def get_health() -> dict:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": "Cannot connect to backend. Check API_BASE_URL."}

def upload_document(file_bytes: bytes, filename: str, content_type: str) -> dict:
    try:
        files = {"file": (filename, file_bytes, content_type)}
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/upload",
            files=files,
            timeout=UPLOAD_TIMEOUT_SECONDS
        )
        if response.status_code != 200:
            return {"error": response.json().get("detail", "Upload failed")}
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def list_documents(skip: int = 0, limit: int = 100, status_filter: str = None) -> dict:
    try:
        params = {"skip": skip, "limit": limit}
        if status_filter:
            params["status"] = status_filter
        response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "total": 0, "documents": []}

def get_document(document_id: int) -> dict:
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/{document_id}",
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_document_chunks(document_id: int, skip: int = 0, limit: int = 20) -> list:
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/{document_id}/chunks",
            params={"skip": skip, "limit": limit},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return []

def delete_document(document_id: int) -> dict:
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/documents/{document_id}",
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def query_documents(query_text: str, top_k: int = 5, document_ids: list = None) -> dict:
    try:
        payload = {"query": query_text, "top_k": top_k}
        if document_ids is not None and len(document_ids) > 0:
            payload["document_ids"] = document_ids
        response = requests.post(
            f"{API_BASE_URL}/api/v1/query/",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_query_history(skip: int = 0, limit: int = 50) -> list:
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/query/history",
            params={"skip": skip, "limit": limit},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return []
