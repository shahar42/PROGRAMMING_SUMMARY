# Sample output 10/95
# Algorithm: find_if_not
# Category: Non-modifying Sequence Operations

"find_if_not": CppFeatureDetail(
    name="std::find_if_not",
    version="C++11",
    description="Finds the first element in a range that does not satisfy the given predicate",
    member_functions={
        "Signature": [
            MemberFunction("find_if_not(first, last, pred)", "Returns iterator to first element where pred(element) is false", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator",
        "UnaryPredicate: must be callable with an element and return convertible to bool",
        "Returns last if no such element is found",
    ]
),