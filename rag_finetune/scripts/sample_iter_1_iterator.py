# Sample output 1/12
# Iterator: iterator
# Category: Iterator Types

"iterator": CppFeatureDetail(
    name="std::iterator",
    version="C++98",
    description="Base class template for defining iterator types with category and type traits",
    member_functions={
        "Constructors": [
            MemberFunction("iterator()", "Default constructor", "O(1)"),
            MemberFunction("iterator(const iterator& other)", "Copy constructor", "O(1)"),
        ],
        "Operations": [],
        "Member Functions": [
            MemberFunction("iterator_category", "Typedef for iterator category", "N/A"),
            MemberFunction("value_type", "Typedef for value type", "N/A"),
            MemberFunction("difference_type", "Typedef for difference type", "N/A"),
            MemberFunction("pointer", "Typedef for pointer type", "N/A"),
            MemberFunction("reference", "Typedef for reference type", "N/A"),
        ],
    },
    notes=[
        "Iterator category: Specifies traits for InputIterator/OutputIterator/ForwardIterator/BidirectionalIterator/RandomAccessIterator",
        "Header: <iterator>",
        "Template: template <class Category, class T, class Distance = ptrdiff_t, class Pointer = T*, class Reference = T&>",
        "Deprecated in C++17; use std::iterator_traits instead for customization",
        "Used as base class: struct MyIter : std::iterator<InputIterator, T> {}",
    ]
),