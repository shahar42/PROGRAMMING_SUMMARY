# C++ STL Containers Extraction Engine Architecture

## Overview

The `extract_cpp_stl_containers.py` script is a sophisticated multi-model book extraction engine that processes PDF books to extract atomic programming concepts. It uses a round-robin approach across multiple AI models (Grok, GPT-4, Gemini) to ensure diverse concept extraction.

## Core Architecture Pattern

### 1. **Multi-Model Rotation System**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     GROK        │    │      GPT-4      │    │     GEMINI      │
│   Processor     │ -> │   Processor     │ -> │   Processor     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ^                                                │
        │                                                │
        └────────────────────────────────────────────────┘
                    Round-Robin Rotation
```

### 2. **Processing Pipeline**
```
PDF Input -> Structure Extraction -> Concept Detection -> Multi-Model Processing -> Deduplication -> File Output
```

## Model API Integration

### API Import Structure
The engine imports three processor classes that handle different AI models:

```python
from processors.grok_processor import GrokAtomicProcessor
from processors.gpt4_nano_processor import GPT4NanoAtomicProcessor
from processors.gemini_processor import GeminiAtomicProcessor
```

### Model Initialization Process

#### 1. **Grok Integration**
```python
# Environment variable loading
grok_key = os.getenv("GROK_API_KEY")

# Debug logging for API key validation
print(f"🔍 DEBUG: Raw GROK_API_KEY length: {len(grok_key) if grok_key else 0}")
print(f"🔍 DEBUG: GROK_API_KEY first 15: {grok_key[:15] if grok_key else 'None'}")

# Processor initialization
if grok_key:
    self.processors["grok"] = GrokAtomicProcessor(grok_key)
    self.model_order.append("grok")
```

#### 2. **GPT-4 Integration**
```python
# OpenAI API key loading
openai_key = os.getenv("OPENAI_API_KEY")

# Processor initialization
if openai_key:
    self.processors["gpt"] = GPT4NanoAtomicProcessor(openai_key)
    self.model_order.append("gpt")
```

#### 3. **Gemini Integration**
```python
# Gemini API key loading
gemini_key = os.getenv("GEMINI_API_KEY")

# Processor initialization
if gemini_key:
    self.processors["gemini"] = GeminiAtomicProcessor(gemini_key)
    self.model_order.append("gemini")
```

### API Usage Patterns

#### Model-Specific Processing Logic
Each model has its own processing approach in `_process_concept()`:

**Grok API Usage:**
```python
elif model_name == "grok":
    # Direct API call with custom prompt
    prompt = self._build_expert_prompt(concept["raw_content"])
    response = processor._call_grok_api(prompt)
    return self._parse_grok_response(response)
```

**GPT-4 API Usage:**
```python
elif model_name == "gpt":
    # Uses existing process_concept method
    return processor.process_concept(concept, "cpp_standard")
```

**Gemini API Usage:**
```python
elif model_name == "gemini":
    # Direct model.generate_content() call
    prompt = self._build_expert_prompt(concept["raw_content"])
    response = processor.model.generate_content(prompt).text
    return self._parse_gemini_response(response)
```

### Response Parsing Strategies

#### Grok Response Parser
```python
def _parse_grok_response(self, response_text):
    try:
        # Regex-based JSON extraction
        match = re.search(r'{.*}', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            concept = json.loads(json_str)
            if 'topic' in concept:
                print(f"✅ GROK extracted expert concept: {concept['topic']}")
                return concept
    except json.JSONDecodeError as e:
        print(f"❌ Failed to decode JSON from Grok: {e}")
        return None
```

#### Gemini Response Parser
```python
def _parse_gemini_response(self, response_text):
    try:
        # Similar regex approach with enhanced debugging
        match = re.search(r'{.*}', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            concept = json.loads(json_str)
            if 'topic' in concept:
                print(f"✅ GEMINI extracted expert concept: {concept['topic']}")
                return concept

        # Debug output for failed parsing
        print(f"🔍 GEMINI RAW RESPONSE:")
        print(f"{'='*50}")
        print(response_text[:1000])  # Show first 1000 chars
        print(f"📏 Total length: {len(response_text)} characters")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to decode JSON from Gemini: {e}")
        return None
```

### Error Handling and Fallbacks

The engine implements robust error handling for API failures:

```python
def _process_concept(self, concept, processor, model_name):
    try:
        # Model-specific processing logic here
        pass
    except Exception as e:
        print(f"❌ Error with {model_name}: {e}")
        return None
```

### API Configuration Requirements

#### Environment File Structure (.env)
```bash
# Grok AI API Key
GROK_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key (for GPT-4)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Gemini API Key
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### API Key Validation
The engine validates API keys during initialization:
```python
if not self.processors:
    raise ValueError("No API keys found!")

print(f"🔄 Round-robin order: { ' → '.join(self.model_order)}")
```

## Key Components

### 1. **CppChapterMapper**
- **Purpose**: Maps content to appropriate C++ chapters/categories
- **Logic**: Uses keyword-based scoring to classify content into chapters like `basic`, `classes`, `templates`, `library`, etc.
- **Extensibility**: Easy to modify `CHAPTER_MAPPING` for different book structures

### 2. **MultiModelRotator**
- **Purpose**: Manages round-robin distribution across AI models
- **Features**:
  - Automatic API key detection
  - Fair distribution of concepts across models
  - Graceful fallback if models are unavailable
- **Models Supported**: Grok, GPT-4 Nano, Gemini

### 3. **CppExpertExtractionEngine**
- **Core Logic**: Main orchestration class
- **Key Features**:
  - Progress tracking with resume capability
  - Duplicate detection using ConceptMemoryManager
  - Expert-level prompt engineering
  - Session-based extraction with summaries

### 4. **ConceptMemoryManager Integration**
- **Deduplication**: Prevents extracting similar concepts
- **Memory**: Maintains concept index across sessions
- **Similarity**: Uses semantic similarity for duplicate detection

## Extraction Process Flow

### Phase 1: Initialization
1. Load API keys from `config/config.env`
2. Initialize processors for available models
3. Set up progress tracking and output directories
4. Initialize concept memory for deduplication

### Phase 2: Content Extraction
1. **PDF Processing**: Extract structured content from PDF starting from last processed page
2. **Concept Detection**: Use `ConceptBoundaryDetector` to identify atomic concepts
3. **Model Assignment**: Round-robin assignment of concepts to different AI models

### Phase 3: Concept Processing
For each detected concept:
1. **Model Selection**: Get next processor in rotation
2. **Expert Prompt**: Build specialized prompt focusing on implementation details
3. **API Call**: Process concept through selected model
4. **Response Parsing**: Extract JSON from model response
5. **Duplicate Check**: Verify concept isn't already extracted
6. **File Save**: Save unique concepts with metadata

### Phase 4: Session Completion
1. **Progress Update**: Save current page and concept count
2. **Summary Generation**: Create markdown summary with model statistics
3. **Duplicate Report**: Optional analysis of similar concepts

## Expert Prompt Strategy

The engine uses expert-level prompts focusing on:
- **Implementation Details**: How compiler implements features
- **Memory Layout**: Performance implications and memory organization
- **Assembly Behavior**: Low-level runtime characteristics
- **Compile-time vs Runtime**: Behavioral distinctions

## File Naming Convention

```
stl_{chapter}_{number}_{safe_topic}.json
```

Example: `stl_templates_003_template_specialization_advanced.json`

## Configuration Requirements

### Environment Variables (.env file)
```bash
GROK_API_KEY=xai-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

### Directory Structure
```
project_root/
├── config/config.env
├── outputs/cpp_stl_containers/
├── core/
│   ├── progress_tracker.py
│   ├── pdf_extractor.py
│   └── concept_detector.py
├── processors/
│   ├── grok_processor.py
│   ├── gpt4_nano_processor.py
│   ├── gemini_processor.py
│   └── concept_memory.py
└── books/extract_cpp_stl_containers.py
```

## Replication Guide for New Books

To adapt this engine for a different book:

### 1. **Create New Chapter Mapper**
```python
class NewBookChapterMapper:
    CHAPTER_MAPPING = {
        "chapter1": ["keyword1", "keyword2"],
        "chapter2": ["keyword3", "keyword4"],
        # Customize based on book structure
    }
```

### 2. **Modify Prompt Strategy**
Update `_build_expert_prompt()` to focus on the new book's domain:
```python
def _build_expert_prompt(self, content):
    return f"""You are an expert in [DOMAIN] creating training data...

    FOCUS ON:
    - Domain-specific implementation details
    - Key concepts relevant to [FIELD]
    - Practical examples and edge cases

    [Rest of prompt structure remains same]
    """
```

### 3. **Update File Naming**
Modify `_save_concept()` to use appropriate prefix:
```python
filename = f"newbook_{concept_id}_{safe_topic}.json"
```

### 4. **Adjust Metadata**
Update extraction metadata in `_save_concept()`:
```python
concept["extraction_metadata"].update({
    "source": "New Book Title and Edition",
    "chapter": chapter_prefix,
    "extraction_type": "domain_specific",
    "extraction_date": datetime.now().isoformat()
})
```

### 5. **Configure PDF Path**
Update the main function:
```python
def main():
    pdf_path = "/path/to/new/book.pdf"
    output_dir = "/path/to/outputs/new_book"
    # Rest remains same
```

## Key Advantages of This Architecture

1. **Multi-Model Resilience**: No single point of failure
2. **Expert-Level Focus**: Specialized prompts for deep technical concepts
3. **Deduplication**: Prevents concept repetition across sessions
4. **Resumable**: Progress tracking allows interrupted sessions to resume
5. **Modular Design**: Easy to swap components or add new models
6. **Comprehensive Logging**: Detailed progress and error reporting

## Performance Considerations

- **Rate Limiting**: Built-in handling for API rate limits
- **Memory Management**: Efficient concept indexing and similarity checking
- **Batch Processing**: Configurable max_concepts per session
- **Error Recovery**: Graceful handling of API failures with model fallback

This architecture provides a robust, scalable foundation for extracting high-quality atomic concepts from technical books across different domains.