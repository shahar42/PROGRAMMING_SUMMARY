# Sample output 10/12
# Iterator: ostream_iterator
# Category: Stream Iterators

"ostream_iterator": CppFeatureDetail(
    name="std::ostream_iterator",
    version="C++98",
    description="Output iterator that writes elements to an output stream",
    member_functions={
        "Constructors": [
            MemberFunction("ostream_iterator(basic_ostream<charT, traits>& s)", "Construct with output stream", "O(1)"),
            MemberFunction("ostream_iterator(basic_ostream<charT, traits>& s, const charT* delimiter)", "Construct with stream and optional delimiter", "O(1)"),
            MemberFunction("ostream_iterator(const ostream_iterator& x)", "Copy constructor", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator=(const T& x)", "Extract and write value to stream, append delimiter if set", "O(1)"),
            MemberFunction("operator*()", "Return reference to self (required for output iterator)", "O(1)"),
            MemberFunction("operator++()", "No-op, return reference to self", "O(1)"),
            MemberFunction("operator++(int)", "No-op, return copy of self", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: OutputIterator",
        "Header: <iterator>",
        "Template parameters: class T (value type), class charT = char, class traits = char_traits<charT>",
        "No comparison operators; stream reference must outlive iterator",
        "Commonly used with std::copy for streaming ranges",
    ]
),