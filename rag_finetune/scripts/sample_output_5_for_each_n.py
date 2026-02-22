# Sample output 5/95
# Algorithm: for_each_n
# Category: Non-modifying Sequence Operations

"for_each_n": CppFeatureDetail(
    name="std::for_each_n",
    version="C++17",
    description="Applies a function object to the first n elements in a range",
    member_functions={
        "Signature": [
            MemberFunction("for_each_n(first, n, f)", "Apply f to each element in [first, first + n)", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for first",
        "n must be a non-negative integer type",
        "Returns InputIterator advanced by n",
        "Function f must be callable with dereferenced InputIterator",
    ]
),