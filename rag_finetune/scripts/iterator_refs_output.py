# Add to DETAIL_DATA in concpp.py:

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

"const_iterator": CppFeatureDetail(
    name="container::const_iterator",
    version="C++98",
    description="Const iterator type provided by containers for read-only traversal",
    member_functions={
        "Constructors": [
            MemberFunction("const_iterator()", "Default constructor (singular)", "O(1)"),
            MemberFunction("const_iterator(iterator)", "Copy constructor from mutable iterator", "O(1)"),
            MemberFunction("const_iterator(const_iterator&)", "Copy constructor", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Dereference to const reference", "O(1)"),
            MemberFunction("operator->", "Member access to const object", "O(1)"),
            MemberFunction("operator++", "Pre-increment", "O(1)"),
            MemberFunction("operator++(int)", "Post-increment", "O(1)"),
            MemberFunction("operator--", "Pre-decrement (bidirectional+)", "O(1)"),
            MemberFunction("operator--(int)", "Post-decrement (bidirectional+)", "O(1)"),
            MemberFunction("operator==", "Equality comparison", "O(1)"),
            MemberFunction("operator!=", "Inequality comparison", "O(1)"),
            MemberFunction("operator<", "Less-than comparison (random access)", "O(1)"),
            MemberFunction("operator<=", "Less-than-or-equal (random access)", "O(1)"),
            MemberFunction("operator>", "Greater-than comparison (random access)", "O(1)"),
            MemberFunction("operator>=", "Greater-than-or-equal (random access)", "O(1)"),
            MemberFunction("operator-", "Difference (random access)", "O(1)"),
            MemberFunction("operator+=", "Addition assignment (random access)", "O(1)"),
            MemberFunction("operator-=", "Subtraction assignment (random access)", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: Matches the container's mutable iterator category (Input/Forward/Bidirectional/RandomAccess)",
        "Header: Container-specific (e.g., <vector>, <list>, <map>)",
        "Provides const access: operator* returns const T&, prevents modification",
        "Convertible from mutable iterator but not vice versa",
        "Not a standalone std:: type; defined as nested type in containers",
    ]
),

"reverse_iterator": CppFeatureDetail(
    name="std::reverse_iterator",
    version="C++98",
    description="Iterator adaptor for reverse traversal",
    member_functions={
        "Constructors": [
            MemberFunction("reverse_iterator()", "Default constructor", "O(1)"),
            MemberFunction("reverse_iterator(iter)", "Construct from base iterator", "O(1)"),
            MemberFunction("reverse_iterator(Iter current)", "Construct from current iterator position", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Dereference to element", "O(1)"),
            MemberFunction("operator++", "Pre-increment: move to previous element", "O(1)"),
            MemberFunction("operator++(int)", "Post-increment: move to previous element", "O(1)"),
            MemberFunction("operator--", "Pre-decrement: move to next element", "O(1)"),
            MemberFunction("operator--(int)", "Post-decrement: move to next element", "O(1)"),
            MemberFunction("operator->", "Member access through dereference", "O(1)"),
            MemberFunction("operator==", "Compare for equality with another reverse_iterator", "O(1)"),
            MemberFunction("operator!=", "Compare for inequality", "O(1)"),
        ],
        "Member Functions": [
            MemberFunction("base()", "Return underlying iterator (one past the current position)", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: Same as base iterator (requires BidirectionalIterator or better)",
        "Header: <iterator>",
        "Reverses traversal direction: ++ on reverse_iterator moves backward in the base sequence",
        "Supports bidirectional operations on the base iterator",
    ]
),

"const_reverse_iterator": CppFeatureDetail(
    name="std::const_reverse_iterator",
    version="C++98",
    description="Const iterator adaptor for reverse traversal of containers",
    member_functions={
        "Constructors": [
            MemberFunction("const_reverse_iterator()", "Default constructor", "O(1)"),
            MemberFunction("const_reverse_iterator(const_iterator)", "Construct from base const iterator", "O(1)"),
            MemberFunction("const_reverse_iterator(reverse_iterator)", "Construct from non-const reverse iterator", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Dereference to const element", "O(1)"),
            MemberFunction("operator++", "Move to previous element (pre-increment)", "O(1)"),
            MemberFunction("operator++(int)", "Move to previous element (post-increment)", "O(1)"),
            MemberFunction("operator--", "Move to next element (pre-decrement)", "O(1)"),
            MemberFunction("operator--(int)", "Move to next element (post-decrement)", "O(1)"),
            MemberFunction("operator->", "Access member through const pointer", "O(1)"),
            MemberFunction("operator==", "Compare for equality", "O(1)"),
            MemberFunction("operator!=", "Compare for inequality", "O(1)"),
        ],
        "Member Functions": [
            MemberFunction("base()", "Get underlying const iterator", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: Matches base const iterator category (BidirectionalIterator or better)",
        "Header: <iterator>",
        "Provides const access during reverse traversal",
        "Typically used with const containers or to enforce const correctness",
        "Equivalent to std::reverse_iterator<ConstIterator>",
    ]
),

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

"front_inserter": CppFeatureDetail(
    name="std::front_inserter",
    version="C++98",
    description="Function creating an output iterator that inserts at the front of a container",
    member_functions={
        "Constructors": [
            MemberFunction("front_inserter(Container& x)", "Returns insert_iterator<Container> inserting at x.begin()", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Returns reference to the iterator itself", "O(1)"),
            MemberFunction("operator++", "Advances iterator (maintains insertion at begin())", "O(1)"),
            MemberFunction("operator++(int)", "Post-increment (maintains insertion at begin())", "O(1)"),
            MemberFunction("operator=(const T& val)", "Inserts val at container front via push_front", "Amortized O(1)"),
            MemberFunction("operator=(T&& val)", "Moves and inserts val at container front", "Amortized O(1)"),
        ],
    },
    notes=[
        "Iterator category: OutputIterator",
        "Header: <iterator>",
        "Requires Container with push_front member",
        "Used with algorithms like std::copy for front insertion into deque or list",
        "Insertion position always at begin(); ++ has no effect on position",
    ]
),

"inserter": CppFeatureDetail(
    name="std::inserter",
    version="C++98",
    description="Function creating an insert_iterator adaptor for container insertion",
    member_functions={
        "Functions": [
            MemberFunction("inserter(Container& cont, Iterator it)", "Returns insert_iterator that inserts before 'it' in 'cont'", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator=(const T& val)", "Inserts 'val' into container at current position", "Amortized O(1)"),
            MemberFunction("operator*()", "Returns *this for assignment compatibility", "O(1)"),
            MemberFunction("operator++()", "Advances insertion iterator (no-op for insert_iterator)", "O(1)"),
            MemberFunction("operator++(int)", "Post-increment (no-op for insert_iterator)", "O(1)"),
        ],
    },
    notes=[
        "Returns: std::insert_iterator<Container>",
        "Iterator category: OutputIterator",
        "Header: <iterator>",
        "Used with algorithms like std::copy for inserting into containers like std::list or std::map",
        "Insertion point advances after each assignment",
    ]
),

"move_iterator": CppFeatureDetail(
    name="std::move_iterator",
    version="C++11",
    description="Iterator adaptor that converts lvalue references to rvalue references for move semantics",
    member_functions={
        "Constructors": [
            MemberFunction("move_iterator() noexcept", "Default constructor", "O(1)"),
            MemberFunction("move_iterator(Iter i) noexcept", "Construct from base iterator", "O(1)"),
            MemberFunction("move_iterator(const move_iterator& other) noexcept", "Copy constructor", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*() const", "Dereference to rvalue reference", "O(1)"),
            MemberFunction("operator->() const", "Arrow operator to underlying element", "O(1)"),
            MemberFunction("operator++()", "Pre-increment underlying iterator", "O(1)"),
            MemberFunction("operator++(int)", "Post-increment underlying iterator", "O(1)"),
            MemberFunction("operator--()", "Pre-decrement (if bidirectional)", "O(1)"),
            MemberFunction("operator--(int)", "Post-decrement (if bidirectional)", "O(1)"),
            MemberFunction("operator==(const move_iterator& other) const", "Equality comparison via base", "O(1)"),
            MemberFunction("operator!=(const move_iterator& other) const", "Inequality comparison via base", "O(1)"),
        ],
        "Member Functions": [
            MemberFunction("base() const noexcept", "Return underlying base iterator", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: Same as base iterator (InputIterator/ForwardIterator/BidirectionalIterator/RandomAccessIterator)",
        "Header: <iterator>",
        "Dereference yields rvalue reference: decltype(*base()) &&",
        "Used with std::make_move_iterator for efficient moves in algorithms",
    ]
),

"istream_iterator": CppFeatureDetail(
    name="std::istream_iterator",
    version="C++98",
    description="Input iterator adaptor for reading objects from an istream",
    member_functions={
        "Constructors": [
            MemberFunction("istream_iterator()", "Default constructor (past-the-end iterator)", "O(1)"),
            MemberFunction("istream_iterator(istream_type& s, const char_type* delim = 0)", "Construct and bind to input stream with optional delimiter", "O(1)"),
            MemberFunction("istream_iterator(const istream_iterator& other)", "Copy constructor", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Dereference to read and return next value using >>", "O(1) amortized"),
            MemberFunction("operator++", "Pre-increment: advance to next value", "O(1) amortized"),
            MemberFunction("operator++(int)", "Post-increment: advance to next value", "O(1) amortized"),
            MemberFunction("operator==", "Equality comparison", "O(1)"),
            MemberFunction("operator!=", "Inequality comparison", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: InputIterator",
        "Header: <iterator>",
        "Reads whitespace-separated values by default; fails when extraction returns false",
        "Past-the-end when default-constructed or stream reaches EOF/failure",
        "Template parameter T must support istream& >> T",
    ]
),

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

"istreambuf_iterator": CppFeatureDetail(
    name="std::istreambuf_iterator",
    version="C++98",
    description="Input iterator for reading characters from a stream buffer",
    member_functions={
        "Constructors": [
            MemberFunction("istreambuf_iterator()", "Default constructor (singular iterator)", "O(1)"),
            MemberFunction("istreambuf_iterator(basic_streambuf<charT, Traits>* s)", "Construct from stream buffer pointer", "O(1)"),
            MemberFunction("istreambuf_iterator(const basic_istream<charT, Traits>& is)", "Construct from input stream", "O(1)"),
        ],
        "Operations": [
            MemberFunction("operator*", "Dereference to read next character", "O(1)"),
            MemberFunction("operator++", "Pre-increment to next character", "O(1)"),
            MemberFunction("operator++(int)", "Post-increment to next character", "O(1)"),
            MemberFunction("operator==", "Compare for equality", "O(1)"),
            MemberFunction("operator!=", "Compare for inequality", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: InputIterator",
        "Header: <iterator>",
        "Templated on charT and Traits (defaults to char_traits<charT>)",
        "Singular iterator (default-constructed) compares equal to end-of-stream",
        "operator* fails (returns Traits::eof()) if stream is in failure state",
    ]
),

"ostreambuf_iterator": CppFeatureDetail(
    name="std::ostreambuf_iterator",
    version="C++98",
    description="Output iterator that inserts characters into a stream buffer",
    member_functions={
        "Constructors": [
            MemberFunction("ostreambuf_iterator() noexcept", "Default constructor (singular iterator)", "O(1)"),
            MemberFunction("ostreambuf_iterator(ostreambuf_iterator const& other) noexcept", "Copy constructor", "O(1)"),
            MemberFunction("ostreambuf_iterator(basic_streambuf<charT, traits>* s) noexcept", "Construct from stream buffer pointer", "O(1)"),
        ],
        "Operations": [
            MemberFunction("charT& operator*() noexcept", "Returns reference for assignment (proxy)", "O(1)"),
            MemberFunction("ostreambuf_iterator& operator++() noexcept", "Advances iterator (no-op, returns *this)", "O(1)"),
            MemberFunction("ostreambuf_iterator operator++(int) noexcept", "Post-increment (no-op, returns *this)", "O(1)"),
            MemberFunction("ostreambuf_iterator& operator=(charT c)", "Assigns character to stream buffer", "O(1)"),
        ],
        "Member Functions": [
            MemberFunction("bool failed() const noexcept", "Returns true if output failed", "O(1)"),
            MemberFunction("explicit operator bool() const noexcept", "Returns true if valid and not failed", "O(1)"),
        ],
    },
    notes=[
        "Iterator category: OutputIterator",
        "Header: <iterator>",
        "Template: ostreambuf_iterator<charT, traits>",
        "Used for outputting sequences to ostreams via streambuf",
        "Singular iterator if constructed with null streambuf",
    ]
),

