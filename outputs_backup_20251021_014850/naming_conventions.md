Recommended Naming Convention
Primary Format:
{book_code}_{category}_{normalized_topic}_{uniqueid}.json
Rationale Based on Your System:

Book Code Prefix (Required)

kr_ - Kernighan & Ritchie
unix_ - UNIX Environment
link_ - Linkers & Loaders
os_ - Operating Systems
exp_ - Expert C Programming

Why: Your topic detection server and orchestrator route by book source. Having this as a prefix enables O(1) filesystem-level filtering.
Category Code (Required)

mem_ - Memory management
ptr_ - Pointers
proc_ - Process management
io_ - Input/Output
sync_ - Synchronization
net_ - Networking
bin_ - Binary/linking concepts

Why: Your system already calculates "relevance scores" - categories would accelerate this scoring process.
Normalized Topic (Required)

Same normalization your ConceptMemoryManager uses: topic.lower().strip().replace(' ', '_').replace('-', '_')
Max 40 characters

Why: Your deduplication system already uses normalized topics for the topic_to_ids index. Matching this in filenames enables direct filesystem searching without loading JSON.
Unique ID (Required)

6-character hash of content

Why: Prevents collisions while keeping names readable. Your system already handles similar concepts with 70-85% similarity thresholds.

Example Names:
kr_mem_malloc_dynamic_allocation_a3f2d1.json
unix_proc_fork_system_call_b8c4e2.json
link_bin_got_plt_mechanism_d5f6a3.json
os_sync_mutex_locks_e7b9c4.json
