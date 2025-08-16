# Project Summary

This project is a Model Context Protocol (MCP) server that provides intelligent access to a comprehensive knowledge base of C programming concepts. The knowledge is extracted and summarized from a collection of authoritative books on C programming, system programming, and computer architecture.

The primary goal is to provide a reliable and efficient way for an AI client to query and learn about complex programming topics, with answers grounded in trusted sources.

# Key Features

*   **Concept-Based Knowledge:** The core of the project is a set of JSON files containing concepts extracted from classic programming books.
*   **Intelligent Search:** Search for specific programming concepts across multiple books.
*   **Concept Comparison:** Compare and contrast different concepts to understand their nuances.
*   **Learning Paths:** Generate structured learning paths for various programming topics.
*   **Personalized Tutorials:** Create custom tutorials tailored to different skill levels.
*   **Code Analysis:** Use the knowledge base to analyze and explain code snippets.
*   **Memory Optimization:** Get strategies and advice on memory optimization techniques.

# Core Components

*   **`mcp_server.py`:** The main server that provides access to the programming concepts knowledge base.
*   **`master_orchestrator_mcp.py`:** An intelligent router that manages specialized, book-specific micro-servers.
*   **`topic_detection_mcp.py`:** A server that analyzes questions to recommend the appropriate micro-server.
*   **PDF Extraction Scripts:** A collection of Python scripts in the `books/` directory responsible for extracting concepts from the source PDF files.
*   **Knowledge Base:** The `outputs/` directory contains the extracted knowledge in JSON format, organized by book.

# Getting Started

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Launch the Main Server:**
    ```bash
    python3 mcp_server.py
    ```
3.  **Interact with the Server:**
    Use an MCP client to connect to the server and start querying the knowledge base.
