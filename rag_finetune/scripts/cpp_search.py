#!/usr/bin/env python3
"""
Enhanced C/C++ Concept Search - Using questionary for better ANSI color support
Usage: cppfind "your question here"
"""

import sys
import json
import pickle
import subprocess
import re
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.live import Live
import questionary
from questionary import Choice, Style
import google.generativeai as genai
from dotenv import load_dotenv

# Configuration paths
BASE_DIR = Path("/home/shahar42/Suumerizing_C_holy_grale_book")
INDEX_FILE = BASE_DIR / "rag_finetune/data/concept_index.pkl"
BOOK_CONFIG_FILE = BASE_DIR / "rag_finetune/config/book_config.json"
# Use the valid API key from the Surf Lamp Agent project
ENV_FILE = Path("/home/shahar42/Git_Surf_Lamp_Agent/.env")

# Load environment variables from .env file
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Try loading from current directory as fallback
    load_dotenv()

# Settings
TOP_K = 50  # Fetch more results for filtering
RERANK_K = 20  # Rerank top 20 results with cross-encoder
DEFAULT_DISPLAY = 10  # Show 10 by default
USE_RERANKER = True  # Enable cross-encoder reranking

console = Console()

# Define custom style for questionary with colored book names
QUESTIONARY_STYLE = Style([
    ("normal", "fg:#FFFFFF"),           # White for normal text
    ("bright_blue", "fg:#5F87FF bold"),      # Bright blue
    ("bright_red", "fg:#FF5F5F bold"),       # Bright red
    ("bright_green", "fg:#5FFF5F bold"),     # Bright green
    ("bright_yellow", "fg:#FFFF5F bold"),    # Bright yellow
    ("bright_magenta", "fg:#FF5FFF bold"),   # Bright magenta
    ("bright_cyan", "fg:#5FFFFF bold"),      # Bright cyan
    ("blue", "fg:#5F87AF bold"),             # Blue
    ("red", "fg:#AF5F5F bold"),              # Red
    ("green", "fg:#5FAF5F bold"),            # Green
    ("yellow", "fg:#AFAF5F bold"),           # Yellow
    ("magenta", "fg:#AF5FAF bold"),          # Magenta
    ("cyan", "fg:#5FAFAF bold"),             # Cyan
    ("grey70", "fg:#BCBCBC bold"),           # Grey
    ("white", "fg:#FFFFFF bold"),            # White
])


def load_book_config() -> Dict:
    """Load book configuration from JSON file"""
    try:
        with open(BOOK_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config['books']
    except FileNotFoundError:
        console.print(f"[yellow]Warning: Book config not found at {BOOK_CONFIG_FILE}[/yellow]")
        return {}
    except Exception as e:
        console.print(f"[red]Error loading book config: {e}[/red]")
        return {}


BOOK_CONFIG = load_book_config()


class ConceptSearch:
    def __init__(self, index_path: Path):
        """Load pre-built index"""
        console.print("\n[dim]Loading concept index...[/dim]")

        with open(index_path, 'rb') as f:
            data = pickle.load(f)

        self.concepts = data["concepts"]
        self.embeddings = data["embeddings"]
        self.model_name = data["model_name"]

        console.print(f"[dim]Loading embedding model: {self.model_name}...[/dim]")
        self.model = SentenceTransformer(self.model_name)

        # Load cross-encoder reranker for better top-K accuracy
        if USE_RERANKER:
            console.print(f"[dim]Loading reranker: ms-marco-MiniLM-L-6-v2...[/dim]")
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        else:
            self.reranker = None

        console.print(f"[green]✓[/green] Ready • {len(self.concepts)} concepts indexed\n")

    def search(self, query: str, top_k: int = TOP_K) -> List[Tuple[Dict, float]]:
        """Search concepts by semantic similarity with keyword boost and reranking"""
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Get initial results
        results = []
        query_words = set(query.lower().split())

        for idx in top_indices:
            concept = self.concepts[idx]
            semantic_score = float(similarities[idx])

            # Load concept JSON to check keywords field
            file_path = Path(concept["file_path"])
            if not file_path.is_absolute():
                file_path = BASE_DIR / file_path

            try:
                with open(file_path, 'r') as f:
                    full_data = json.load(f)

                keywords = full_data.get("keywords", "")

                # Handle keywords as list or string
                if isinstance(keywords, list):
                    keywords = ", ".join(keywords)

                # Count keyword matches
                keyword_boost = 0
                if keywords:
                    keyword_words = set(keywords.lower().replace(",", " ").split())
                    matches = query_words & keyword_words
                    keyword_boost = len(matches) * 0.08  # Boost 0.08 per matched word

                # Combine scores
                final_score = min(semantic_score + keyword_boost, 1.0)  # Cap at 1.0

                results.append((concept, final_score, full_data))
            except Exception:
                # If we can't read the file, just use semantic score
                results.append((concept, semantic_score, None))

        # Re-sort by boosted scores
        results.sort(key=lambda x: x[1], reverse=True)

        # Apply cross-encoder reranking on top-K results
        if self.reranker and len(results) > 0:
            rerank_candidates = results[:RERANK_K]

            # Prepare query-document pairs for reranking
            pairs = []
            for concept, score, full_data in rerank_candidates:
                # Use topic + explanation for reranking
                if full_data:
                    doc_text = f"{concept['topic']}. {full_data.get('explanation', '')[:300]}"
                else:
                    doc_text = concept['topic']
                pairs.append([query, doc_text])

            # Get reranker scores
            rerank_scores = self.reranker.predict(pairs)

            # Update scores: blend original score (60%) with rerank score (40%)
            reranked = []
            for i, (concept, orig_score, full_data) in enumerate(rerank_candidates):
                # Normalize rerank score to [0, 1]
                rerank_score = float(rerank_scores[i])
                normalized_rerank = 1 / (1 + np.exp(-rerank_score))  # Sigmoid

                # Blend scores
                blended_score = 0.6 * orig_score + 0.4 * normalized_rerank
                reranked.append((concept, blended_score))

            # Keep non-reranked results
            remaining = [(c, s) for c, s, _ in results[RERANK_K:]]

            # Combine and sort
            results = reranked + remaining
            results.sort(key=lambda x: x[1], reverse=True)
        else:
            # No reranking - just strip full_data
            results = [(c, s) for c, s, _ in results]

        return results

    def get_book_config(self, book_name: str) -> Dict:
        """Get book configuration with defaults"""
        return BOOK_CONFIG.get(book_name, {
            "color": "white",
            "short": book_name[:15],
            "display": book_name
        })

    def format_result_entry(self, concept: Dict, score: float) -> list:
        """Format a single result entry as token tuples for questionary"""
        book_config = self.get_book_config(concept.get('book', ''))
        topic = concept['topic']
        book_display = book_config['display']
        color = book_config['color']

        # Truncate topic if too long (keep most of the title visible)
        max_topic_len = 80
        if len(topic) > max_topic_len:
            topic = topic[:max_topic_len-3] + "..."

        score_pct = int(score * 100)

        # Return token tuples: (style_class, text)
        # Questionary uses this format instead of inline style tags
        return [
            ("class:normal", f"[{score_pct:3d}%] {topic} "),
            (f"class:{color}", f"[{book_display}]")
        ]

    def display_book_legend(self, results: List[Tuple[Dict, float]]):
        """Display color legend for books found in results"""
        books_in_results = set(concept.get('book', 'Unknown') for concept, _ in results)

        console.print("\n[bold]Book Sources:[/bold]")

        legend_items = []
        for book in sorted(books_in_results):
            config = self.get_book_config(book)
            legend_items.append(f"[{config['color']}]■[/{config['color']}] {config['display']}")

        for i in range(0, len(legend_items), 2):
            if i + 1 < len(legend_items):
                console.print(f"  {legend_items[i]}    {legend_items[i+1]}")
            else:
                console.print(f"  {legend_items[i]}")

        console.print()

    def display_results_table(self, results: List[Tuple[Dict, float]]):
        """Display results as a grouped table by book"""
        by_book = {}
        for concept, score in results:
            book = concept.get('book', 'Unknown')
            if book not in by_book:
                by_book[book] = []
            by_book[book].append((concept, score))

        table = Table(
            title="[bold]Search Results Summary[/bold]",
            show_header=True,
            header_style="bold cyan",
            border_style="dim"
        )

        table.add_column("Book", style="bold")
        table.add_column("Matches", justify="right")
        table.add_column("Top Score", justify="right")

        for book, concepts in sorted(by_book.items(), key=lambda x: -len(x[1])):
            config = self.get_book_config(book)
            top_score = max(score for _, score in concepts)

            table.add_row(
                f"[{config['color']}]■ {config['display']}[/{config['color']}]",
                str(len(concepts)),
                f"{int(top_score * 100)}%"
            )

        console.print("\n")
        console.print(table)
        console.print("\n")

    def display_concept_full(self, concept: Dict, score: float, show_code: bool = False):
        """Display full concept with enhanced formatting"""
        file_path = Path(concept["file_path"])
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path

        with open(file_path, 'r') as f:
            full_data = json.load(f)

        book = concept.get('book', 'Unknown')
        book_config = self.get_book_config(book)

        # Extract clean title for display (remove prepended keywords if present)
        display_topic = concept['topic']
        if ' - ' in display_topic:
            display_topic = display_topic.split(' - ', 1)[1]

        header = Text()
        header.append(display_topic, style="bold white")

        meta_table = Table.grid(padding=(0, 2))
        meta_table.add_column(style="dim")
        meta_table.add_column()

        meta_table.add_row("Source:", f"[{book_config['color']}]{book}[/{book_config['color']}]")
        meta_table.add_row("Match:", f"[green]{int(score * 100)}%[/green]")
        meta_table.add_row("ID:", f"[dim]{concept['id']}[/dim]")

        has_code = full_data.get('code_example') or full_data.get('practical_example')
        if has_code and not show_code:
            meta_table.add_row("Code:", "[green]✓ Available[/green]")

        explanation = full_data.get('explanation', 'No explanation available.')

        panel_content = []
        panel_content.append(meta_table)
        panel_content.append("\n" + "─" * 78 + "\n")
        panel_content.append(Markdown(explanation))

        if show_code:
            code = full_data.get('code_example') or full_data.get('practical_example')
            if code:
                panel_content.append("\n" + "─" * 78 + "\n")
                panel_content.append(Text("Code Example:", style="bold cyan"))
                panel_content.append("\n")

                lang = "cpp" if any(kw in code for kw in ["std::", "class ", "template"]) else "c"
                try:
                    syntax = Syntax(code, lang, theme="monokai", line_numbers=False)
                    panel_content.append(syntax)
                except:
                    panel_content.append(Text(code, style="dim"))

        from rich.console import Group
        panel = Panel(
            Group(*panel_content),
            title=header,
            border_style=book_config['color'],
            padding=(1, 2),
            expand=False
        )

        console.print("\n")
        console.print(panel)
        console.print("\n")

        return full_data

    def _extract_syscall_name(self, concept: Dict) -> Optional[str]:
        """Extract system call name from POSIX syscall concept ID"""
        concept_id = concept.get('id', '')
        match = re.search(r'posix_(?:sys_)?([a-z0-9_]+?)_[a-f0-9]+', concept_id)
        return match.group(1) if match else None

    def _extract_function_name(self, concept_data: Dict) -> Optional[str]:
        """Extract function name from C Standard Library/POSIX API concept"""
        extraction_meta = concept_data.get('extraction_metadata', {})
        return extraction_meta.get('function_name')

    def _show_manpage_section(self, name: str, section: int) -> bool:
        """Generic manpage display using man command"""
        console.print(f"\n[cyan]Opening manpage: {name}({section})[/cyan]\n")

        try:
            result = subprocess.run(['man', str(section), name], check=False)
            return result.returncode == 0
        except FileNotFoundError:
            console.print("[red]✗ 'man' command not found[/red]")
            return False
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False

    def show_manpage(self, concept: Dict, concept_data: Optional[Dict] = None) -> bool:
        """Display manpage for concept (polymorphic: handles both syscalls and C library functions)

        Args:
            concept: Concept metadata dict
            concept_data: Full concept data (loaded from JSON if provided)

        Returns:
            bool: True if manpage was displayed successfully
        """
        book = concept.get('book', '')

        # POSIX System Call Manual (section 2)
        if book == "POSIX System Call Manual":
            syscall = self._extract_syscall_name(concept)
            if not syscall:
                console.print("[red]✗ Could not extract system call name[/red]")
                return False
            return self._show_manpage_section(syscall, 2)

        # C Standard Library and POSIX APIs (section 3)
        elif book == "C Standard Library and POSIX APIs":
            # If full data not provided, load it
            if not concept_data:
                file_path = Path(concept["file_path"])
                if not file_path.is_absolute():
                    file_path = BASE_DIR / file_path
                try:
                    with open(file_path, 'r') as f:
                        concept_data = json.load(f)
                except Exception as e:
                    console.print(f"[red]✗ Could not load concept data: {e}[/red]")
                    return False

            function_name = self._extract_function_name(concept_data)
            if not function_name:
                console.print("[red]✗ Could not extract function name[/red]")
                return False
            return self._show_manpage_section(function_name, 3)

        else:
            console.print(f"[yellow]⚠ Manpages not available for {book}[/yellow]")
            return False


def chat_about_concept(concept_data: Dict, concept_meta: Dict):
    """Interactive chat session about a specific concept using Gemini 2.5 Pro"""

    # Initialize Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("\n[red]✗ GEMINI_API_KEY environment variable not set[/red]")
        console.print("[yellow]Set it with: export GEMINI_API_KEY='your-key'[/yellow]\n")
        console.input("[dim]Press Enter to continue...[/dim]")
        return

    genai.configure(api_key=api_key)

    # Build system context from concept data (hidden from user)
    topic = concept_data.get('topic', 'Unknown Topic')
    explanation = concept_data.get('explanation', '')
    code_example = concept_data.get('code_example', '')
    syntax = concept_data.get('syntax', '')
    example_explanation = concept_data.get('example_explanation', '')
    book = concept_data.get('book', 'Unknown Source')

    system_context = f"""You are an expert programming tutor specializing in C/C++ concepts.

You are currently helping a student understand the following concept:

**Topic**: {topic}
**Source**: {book}

**Concept Explanation**:
{explanation}

"""

    if syntax:
        system_context += f"""**Syntax/Reference**:
{syntax}

"""

    if code_example:
        system_context += f"""**Code Example**:
```
{code_example}
```

"""

    if example_explanation:
        system_context += f"""**Example Explanation**:
{example_explanation}

"""

    system_context += """**Your Role**:
- You are a guru of programming and computer architecture
- Your answers are concise yet dense with information
- Answer questions about this specific concept
- Provide clear, technical explanations without fluff
- Give practical examples when helpful
- Reference the concept material above when relevant
- If asked about something outside this concept, politely redirect to the topic

The student doesn't know you have this context loaded - answer naturally as an expert tutor."""

    # Initialize chat model with system instruction
    model = genai.GenerativeModel(
        'gemini-2.5-flash-preview-09-2025',
        system_instruction=system_context
    )
    chat = model.start_chat(history=[])

    # Display chat header
    console.clear()
    header = Panel(
        f"[bold cyan]Chat about: {topic}[/bold cyan]\n"
        f"[dim]Type 'exit' or 'quit' to return to menu[/dim]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(header)
    console.print()

    # Interactive chat loop
    while True:
        # Get user input
        user_input = questionary.text(
            "You:",
            qmark=">"
        ).ask()

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit', 'q']:
            console.print("\n[cyan]Exiting chat...[/cyan]\n")
            break

        try:
            # Send message and stream response
            console.print()
            bot_panel = Panel(
                "",
                title="[bold green]Assistant[/bold green]",
                border_style="green",
                padding=(1, 2)
            )

            # Stream response
            response_text = ""
            response = chat.send_message(user_input, stream=True)

            # Use Live display for streaming
            with Live(console=console, refresh_per_second=10) as live:
                for chunk in response:
                    if chunk.text:
                        response_text += chunk.text
                        # Update panel with accumulated text
                        updated_panel = Panel(
                            Markdown(response_text),
                            title="[bold green]Assistant[/bold green]",
                            border_style="green",
                            padding=(1, 2)
                        )
                        live.update(updated_panel)

            console.print()
            console.print("[dim]Type 'q' or 'exit' to return to menu[/dim]\n")

        except Exception as e:
            console.print(f"\n[red]✗ Error: {e}[/red]\n")
            continue


def show_concept_detail(searcher: ConceptSearch, concept: Dict, score: float) -> str:
    """Show concept detail and return action"""
    full_data = searcher.display_concept_full(concept, score, show_code=False)

    book = concept.get('book', '')
    has_manpage = book in ["POSIX System Call Manual", "C Standard Library and POSIX APIs"]
    has_code = full_data.get('code_example') or full_data.get('practical_example')

    # Build action choices
    actions = []
    actions.append(Choice("Chat about this concept", value="chat"))
    if has_code:
        actions.append(Choice("View Code Example", value="code"))
    if has_manpage:
        actions.append(Choice("Open Manpage", value="manpage"))
    actions.extend([
        Choice("← Back to Results", value="back"),
        Choice("New Search", value="new"),
        Choice("Quit", value="quit")
    ])

    action = questionary.select(
        "What would you like to do?",
        choices=actions,
        use_shortcuts=True,
        use_arrow_keys=True
    ).ask()

    if action == "chat":
        chat_about_concept(full_data, concept)
        return show_concept_detail(searcher, concept, score)
    elif action == "code":
        searcher.display_concept_full(concept, score, show_code=True)
        console.input("\n[dim]Press Enter to continue...[/dim]")
        return show_concept_detail(searcher, concept, score)
    elif action == "manpage":
        searcher.show_manpage(concept, full_data)
        console.input("\n[dim]Press Enter to continue...[/dim]")
        return show_concept_detail(searcher, concept, score)
    else:
        return action


def get_books_in_results(results: List[Tuple[Dict, float]]) -> List[str]:
    """Extract unique book titles from results, sorted alphabetically"""
    books = {concept.get('book', 'Unknown') for concept, _ in results}
    return sorted(books)


def filter_by_books(results: List[Tuple[Dict, float]], selected_books: List[str]) -> List[Tuple[Dict, float]]:
    """Filter results to only include selected books, preserving order and scores"""
    return [(concept, score) for concept, score in results if concept.get('book') in selected_books]


def prompt_book_selection(searcher: ConceptSearch, results: List[Tuple[Dict, float]]) -> Optional[List[str]]:
    """Show single-select menu for book filtering, return selected book as list or None"""
    available_books = get_books_in_results(results)
    if not available_books:
        return None

    # Build choices
    choices = []
    for book in available_books:
        config = searcher.get_book_config(book)
        count = sum(1 for c, _ in results if c.get('book') == book)
        label = f"{config['display']} ({count} results)"
        choices.append(Choice(title=label, value=book))

    choices.append(Choice("← Cancel (show all books)", value=None))

    selected = questionary.select(
        "Filter to which book?",
        choices=choices,
        style=QUESTIONARY_STYLE
    ).ask()

    return [selected] if selected else None


def interactive_search(searcher: ConceptSearch, initial_query: Optional[str] = None):
    """Main interactive search loop"""

    while True:
        # Get query
        if initial_query:
            query = initial_query
            console.print(f"[bold cyan]→[/bold cyan] {query}\n")
            initial_query = None
        else:
            query = questionary.text(
                "Search:",
                qmark=">"
            ).ask()

            if not query:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

        # Search
        console.print(f"\n[dim]Searching...[/dim]")
        results = searcher.search(query)

        if not results:
            console.print("[red]✗ No results found[/red]\n")
            continue

        # Show legend and summary
        searcher.display_book_legend(results)
        searcher.display_results_table(results)

        # Track original results for filter reset
        original_results = results
        current_results = results
        active_filter = None

        # Limit initial display
        display_results = current_results[:DEFAULT_DISPLAY]

        while True:
            # Build menu choices with token tuples for colored rendering
            choices = []
            for concept, score in display_results:
                entry_tokens = searcher.format_result_entry(concept, score)
                choices.append(Choice(title=entry_tokens, value=("concept", concept, score)))

            # Add action choices (plain strings)
            if len(current_results) > DEFAULT_DISPLAY and len(display_results) < len(current_results):
                choices.append(Choice(f"─── Show All {len(current_results)} Results ───", value=("show_all", None, None)))

            # Filter options
            if active_filter:
                choices.append(Choice(f"Clear Book Filter (showing {len(current_results)}/{len(original_results)})", value=("clear_filter", None, None)))
            else:
                choices.append(Choice("Filter by Book...", value=("filter", None, None)))

            choices.extend([
                Choice("─── View Summary Table ───", value=("summary", None, None)),
                Choice("New Search", value=("new", None, None)),
                Choice("Quit", value=("quit", None, None))
            ])

            # Show menu using questionary with custom style
            # Disable shortcuts if more than 36 choices (questionary limitation)
            use_shortcuts = len(choices) <= 36

            result = questionary.select(
                f"Results for: {query}",
                choices=choices,
                style=QUESTIONARY_STYLE,
                use_shortcuts=use_shortcuts,
                use_arrow_keys=True
            ).ask()

            if result is None or result[0] == "quit":
                console.print("\n[yellow]Goodbye![/yellow]")
                return

            action, concept, score = result

            if action == "new":
                break  # Break inner loop to start new search

            elif action == "summary":
                searcher.display_results_table(current_results)
                console.input("\n[dim]Press Enter to continue...[/dim]")
                continue

            elif action == "filter":
                selected_books = prompt_book_selection(searcher, original_results)
                if selected_books:
                    current_results = filter_by_books(original_results, selected_books)
                    active_filter = selected_books
                    display_results = current_results[:DEFAULT_DISPLAY]
                    book_name = searcher.get_book_config(selected_books[0])['display']
                    console.print(f"\n[green]✓[/green] Showing {len(current_results)} results from {book_name}\n")
                continue

            elif action == "clear_filter":
                # Reset to original results
                current_results = original_results
                active_filter = None
                display_results = current_results[:DEFAULT_DISPLAY]
                console.print(f"\n[green]✓[/green] Filter cleared, showing all {len(original_results)} results\n")
                continue

            elif action == "show_all":
                # Switch to showing all current results
                display_results = current_results
                continue

            elif action == "concept":
                # Show concept detail
                detail_action = show_concept_detail(searcher, concept, score)

                if detail_action == "quit":
                    console.print("\n[yellow]Goodbye![/yellow]")
                    return
                elif detail_action == "new":
                    break  # Break inner loop to start new search
                # "back" just continues the inner loop


def main():
    if not INDEX_FILE.exists():
        console.print(f"[red]✗ Index not found: {INDEX_FILE}[/red]")
        console.print("[yellow]Run: python rag_finetune/scripts/build_concept_index.py[/yellow]")
        sys.exit(1)

    console.print("\n[bold cyan]C/C++ Concept Search[/bold cyan]")
    console.print("[dim]Enhanced semantic search with colored results[/dim]\n")

    try:
        searcher = ConceptSearch(INDEX_FILE)
    except Exception as e:
        console.print(f"[red]✗ Failed to load index: {e}[/red]")
        sys.exit(1)

    initial_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None

    try:
        interactive_search(searcher, initial_query)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted. Goodbye![/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
