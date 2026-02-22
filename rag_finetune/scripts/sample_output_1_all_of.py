# Sample output 1/95
# Algorithm: all_of
# Category: Non-modifying Sequence Operations

"all_of": CppFeatureDetail(
    name="std::all_of",
    version="C++11",
    description="Checks if all elements in the range satisfy the given predicate",
    member_functions={
        "Signature": [
            MemberFunction("all_of(InputIterator first, InputIterator last, Predicate pred)", "Returns true if pred(*i) is true for every iterator i in [first, last)", "O(last - first)"),
        ],
    },
    notes=[
        "Requires InputIterator",
        "Predicate must be a callable type that accepts the value_type and returns convertible to bool",
        "Returns true if [first, last) is empty",
    ]
),