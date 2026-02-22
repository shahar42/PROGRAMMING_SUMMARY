# Sample output 5/12
# Iterator: back_inserter
# Category: Iterator Adaptors

"back_inserter": CppFeatureDetail(
    name="std::back_inserter",
    version="C++98",
    description="Function creating an output iterator that appends elements to the end of a container",
    member_functions={
        "Constructors": [
            MemberFunction("back_inserter(cont)", "Creates back_insert_iterator from container reference", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Returns reference to *this", "O(1)"),
            MemberFunction("operator++", "No-op, returns *this", "O(1)"),
            MemberFunction("operator--", "Not supported"),
            MemberFunction("operator=(const T& x)", "Appends x via container.push_back(x), returns *this", "Amortized O(1)"),
            MemberFunction("operator=(T&& x)", "Appends std::move(x) via container.push_back, returns *this", "Amortized O(1)"),
        ],
    },
    notes=[
        "Iterator category: OutputIterator",
        "Header: <iterator>",
        "Requires container with push_back member (e.g., vector, deque, list)",
        "Used with algorithms like std::copy for appending elements",
        "Does not support dereferencing for reading or random access",
    ]
),