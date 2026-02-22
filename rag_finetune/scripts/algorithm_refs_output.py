# Add to DETAIL_DATA in concpp.py:

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

"any_of": CppFeatureDetail(
    name="std::any_of",
    version="C++11",
    description="Checks if any element in the range satisfies the given predicate",
    member_functions={
        "Signature": [
            MemberFunction("any_of(first, last, pred)", "Sequential version: returns true if pred is true for any element in [first, last)", "O(n)"),
            MemberFunction("any_of(policy, first, last, pred)", "Parallel version (C++17): returns true if pred is true for any element in [first, last)", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator (ForwardIterator for parallel version)",
        "UnaryPredicate must be callable with the element type and convertible to bool",
        "Short-circuits on first true result",
    ]
),

"none_of": CppFeatureDetail(
    name="std::none_of",
    version="C++11",
    description="Checks if none of the elements in a range satisfy the given predicate",
    member_functions={
        "Signature": [
            MemberFunction("none_of(first, last, pred)", "Returns true if pred is false for all elements in [first, last)", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator",
        "UnaryPredicate must be callable with the value type and return convertible to bool",
        "Short-circuits on first true pred result",
    ]
),

"for_each": CppFeatureDetail(
    name="std::for_each",
    version="C++98",
    description="Applies a function to each element in the range [first, last)",
    member_functions={
        "Signature": [
            MemberFunction("for_each(first, last, f)", "Applies function f to each dereferenced iterator in the range", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator",
        "Function f must be callable with the value type of the iterator",
        "In C++20, returns f (moved or copied); pre-C++20 returns void",
        "constexpr in C++20",
        "The order of application is the order of incrementing the iterator",
    ]
),

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

"count": CppFeatureDetail(
    name="std::count",
    version="C++98",
    description="Counts the number of elements in the range equal to a specified value",
    member_functions={
        "Signature": [
            MemberFunction("count(InputIt first, InputIt last, const T& value)", "Counts elements equal to value using operator==", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator",
        "Element requirement: *first is EqualityComparable with T (supports == and !=",
        "Returns difference_type (ptrdiff_t); n is distance from first to last",
    ]
),

"count_if": CppFeatureDetail(
    name="std::count_if",
    version="C++98",
    description="Counts elements in a range that satisfy a given predicate",
    member_functions={
        "Signature": [
            MemberFunction("count_if(first, last, pred)", "Count elements for which pred returns true", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator",
        "UnaryPredicate: must accept an element of the range and return convertible to bool",
        "Returns difference_type: number of elements satisfying the predicate",
    ]
),

"find": CppFeatureDetail(
    name="std::find",
    version="C++98",
    description="Searches for the first element in a range equal to a given value",
    member_functions={
        "Signature": [
            MemberFunction("find(first, last, value)", "Returns iterator to first element equal to value, or last if not found", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator",
        "Elements must be equality comparable with value (operator==)",
        "Performs linear search",
    ]
),

"find_if": CppFeatureDetail(
    name="std::find_if",
    version="C++98",
    description="Finds the first element in a range that satisfies a given predicate",
    member_functions={
        "Signature": [
            MemberFunction("find_if(first, last, pred)", "Returns iterator to first element where pred(element) is true, or last if none", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator",
        "UnaryPredicate: callable with element type returning convertible to bool",
        "Linear search from first to last",
    ]
),

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

"find_end": CppFeatureDetail(
    name="std::find_end",
    version="C++98",
    description="Finds the last occurrence of a subsequence in a range",
    member_functions={
        "Signature": [
            MemberFunction("find_end(first1, last1, first2, last2)", "Finds last match using operator==", "O((last1-first1)*(last2-first2))"),
            MemberFunction("find_end(first1, last1, first2, last2, pred)", "Finds last match using binary predicate", "O((last1-first1)*(last2-first2))"),
        ],
    },
    notes=[
        "Requires ForwardIterator for both ranges",
        "Elements must be EqualityComparable for default overload",
        "Returns last1 if no subsequence is found",
        "Searches from the end of the first range",
    ]
),

"find_first_of": CppFeatureDetail(
    name="std::find_first_of",
    version="C++98",
    description="Finds the first element in a range that matches any element in another range",
    member_functions={
        "Signature": [
            MemberFunction("find_first_of(first1, last1, first2, last2)", "Searches [first1, last1) for any element equal to those in [first2, last2)", "O((last1-first1)*(last2-first2))"),
            MemberFunction("find_first_of(first1, last1, first2, last2, pred)", "Uses binary predicate pred for matching", "O((last1-first1)*(last2-first2))"),
        ],
    },
    notes=[
        "Requires InputIterator for both [first1, last1) and [first2, last2)",
        "Elements must be EqualityComparable for the first overload",
        "Returns last1 if no match is found",
        "The second range [first2, last2) is traversed multiple times",
    ]
),

"adjacent_find": CppFeatureDetail(
    name="std::adjacent_find",
    version="C++98",
    description="Finds the first pair of adjacent equal elements in a range",
    member_functions={
        "Signature": [
            MemberFunction("adjacent_find(first, last)", "Finds adjacent elements equal via operator==", "O(n)"),
            MemberFunction("adjacent_find(first, last, pred)", "Finds adjacent elements matching binary predicate pred", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator",
        "Default overload requires EqualityComparable elements",
        "Returns last if no such pair found",
    ]
),

"search": CppFeatureDetail(
    name="std::search",
    version="C++98",
    description="Searches for a subsequence within a sequence",
    member_functions={
        "Signature": [
            MemberFunction("search(first, last, s_first, s_last)", "Searches using operator==", "O((last-first)*(s_last-s_first))"),
            MemberFunction("search(first, last, s_first, s_last, pred)", "Searches using binary predicate", "O((last-first)*(s_last-s_first))"),
        ],
    },
    notes=[
        "Requires ForwardIterator for all iterators",
        "Elements must be EqualityComparable for default version",
        "Returns iterator to start of subsequence or last if not found",
        "Subsequence [s_first, s_last) must be non-empty",
    ]
),

"search_n": CppFeatureDetail(
    name="std::search_n",
    version="C++98",
    description="Searches for a sequence of n consecutive elements equal to a value",
    member_functions={
        "Signature": [
            MemberFunction("search_n(first, last, count, value)", "Searches for count consecutive elements equal to value using ==", "O(last - first)"),
            MemberFunction("search_n(first, last, count, value, pred)", "Searches for count consecutive elements satisfying pred with value", "O(last - first)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Value type must be EqualityComparable with T for first overload",
        "BinaryPredicate must induce an equivalence relation for second overload",
        "Returns last if no such sequence is found",
    ]
),

"mismatch": CppFeatureDetail(
    name="std::mismatch",
    version="C++98",
    description="Finds the first position where two ranges differ",
    member_functions={
        "Signature": [
            MemberFunction("mismatch(first1, last1, first2)", "Compares elements using operator== until mismatch or end", "O(n) where n = distance(first1, last1)"),
            MemberFunction("mismatch(first1, last1, first2, pred)", "Compares elements using binary predicate pred until mismatch or end", "O(n) where n = distance(first1, last1)"),
        ],
    },
    notes=[
        "Requires InputIterator for all iterators",
        "Elements must be EqualityComparable for default overload (operator==)",
        "Returns pair of iterators to first mismatch; if no mismatch, returns {last1, first2 + (last1 - first1)}",
        "In C++14, additional overloads with ExecutionPolicy for parallel execution",
    ]
),

"copy": CppFeatureDetail(
    name="std::copy",
    version="C++98",
    description="Copies elements from a source range to a destination range",
    member_functions={
        "Signature": [
            MemberFunction("copy(InputIt first, InputIt last, OutputIt d_first)", "Copies elements from [first, last) to the range starting at d_first", "O(last - first)"),
        ],
    },
    notes=[
        "Requires InputIterator for first and last; OutputIterator for d_first",
        "Value type of InputIterator must be CopyAssignable to value type of OutputIterator",
        "Destination range must have at least (last - first) elements available; behavior is undefined otherwise",
        "Returns OutputIt pointing to the end of the destination range",
    ]
),

"copy_if": CppFeatureDetail(
    name="std::copy_if",
    version="C++11",
    description="Copies elements from the input range that satisfy a predicate to the output range",
    member_functions={
        "Signature": [
            MemberFunction("copy_if(first, last, d_first, pred)", "Copies elements [first, last) satisfying pred to [d_first, ...)", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for d_first",
        "UnaryPredicate must be callable with the value type of InputIterator",
        "Output range must have sufficient space; no bounds checking",
        "Elements are copied via assignment",
    ]
),

"copy_n": CppFeatureDetail(
    name="std::copy_n",
    version="C++11",
    description="Copies exactly n elements from input range to output range",
    member_functions={
        "Signature": [
            MemberFunction("copy_n(first, n, result)", "Copies n elements starting from first to result", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for first and OutputIterator for result",
        "Elements must be CopyAssignable",
        "Undefined behavior if n < 0",
        "Returns OutputIterator pointing to the end of the output range",
    ]
),

"copy_backward": CppFeatureDetail(
    name="std::copy_backward",
    version="C++98",
    description="Copies elements from a source range to a destination range in reverse order",
    member_functions={
        "Signature": [
            MemberFunction("copy_backward(first, last, result)", "Copies [first, last) backwards to result", "O(last - first)"),
        ],
    },
    notes=[
        "Requires BidirectionalIterator for input and output ranges",
        "Value types must be CopyAssignable",
        "Destination range must not overlap with source in a way that invalidates iterators; result should point to one past the last destination element",
    ]
),

"move": CppFeatureDetail(
    name="std::move",
    version="C++11",
    description="Transfers elements from one range to another using move semantics",
    member_functions={
        "Signature": [
            MemberFunction("move(InputIt first, InputIt last, OutputIt d_first)", "Moves elements from [first, last) to [d_first, d_first + (last - first))", "O(last - first)"),
            MemberFunction("move(ExecutionPolicy&& policy, InputIt first, InputIt last, OutputIt d_first)", "Moves elements with execution policy (C++17)", "O(last - first)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator for source range, OutputIterator for destination",
        "Element requirement: MoveConstructible and MoveAssignable via iterators",
        "Source and destination ranges must not overlap; otherwise, undefined behavior",
        "Uses std::move on each element",
    ]
),

"move_backward": CppFeatureDetail(
    name="std::move_backward",
    version="C++11",
    description="Moves elements from [first, last) to the range ending at result using move semantics",
    member_functions={
        "Signature": [
            MemberFunction("move_backward(first, last, result)", "Moves range backwards to avoid overwriting on overlap", "O(n)"),
        ],
    },
    notes=[
        "Requires BidirectionalIterator for first and last, OutputIterator for result",
        "Elements must be MoveConstructible and MoveAssignable",
        "Input and output ranges may overlap; moves from end to beginning",
    ]
),

"fill": CppFeatureDetail(
    name="std::fill",
    version="C++98",
    description="Assigns a given value to every element in a range",
    member_functions={
        "Signature": [
            MemberFunction("fill(InputIterator first, InputIterator last, const T& value)", "Assigns value to each element in [first, last)", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator",
        "Elements must be Assignable from T",
        "Modifies elements in place",
    ]
),

"fill_n": CppFeatureDetail(
    name="std::fill_n",
    version="C++98",
    description="Assigns a given value to the first n elements starting from an output iterator",
    member_functions={
        "Signature": [
            MemberFunction("fill_n(first, n, value)", "Assigns value to [first, first + n); returns first + n", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: OutputIterator",
        "Value must be assignable to *first",
        "Behavior is undefined if n < 0",
        "n is of type std::iter_difference_t<OutputIterator> in C++20+",
    ]
),

"transform": CppFeatureDetail(
    name="std::transform",
    version="C++98",
    description="Applies a function to a range and stores results in another range",
    member_functions={
        "Signature": [
            MemberFunction("transform(first, last, result, unary_op)", "Apply unary operation to each element in [first, last)", "O(n)"),
            MemberFunction("transform(first1, last1, first2, result, binary_op)", "Apply binary operation to corresponding elements from two ranges", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for input ranges, OutputIterator for result",
        "For binary overload, second range must have at least (last1 - first1) elements",
        "Input ranges are not modified",
        "unary_op must be callable as T(const Type1&)",
        "binary_op must be callable as T(const Type1&, const Type2&)",
    ]
),

"generate": CppFeatureDetail(
    name="std::generate",
    version="C++98",
    description="Assigns values from a generator function to a range of elements",
    member_functions={
        "Signature": [
            MemberFunction("generate(ForwardIterator first, ForwardIterator last, Generator gen)", "Assigns gen() to each element in [first, last)", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Generator must be callable with () and return type assignable to *first",
        "Elements must be Assignable"
    ]
),

"generate_n": CppFeatureDetail(
    name="std::generate_n",
    version="C++98",
    description="Assigns values from a generator function to the first n elements of a range",
    member_functions={
        "Signature": [
            MemberFunction("generate_n(first, n, gen)", "Assigns gen() to [first, first + n)", "O(n)"),
        ],
    },
    notes=[
        "Requires OutputIterator for first",
        "gen must be callable with no arguments and return type assignable to *first",
        "Advances first by n positions and returns the new first",
    ]
),

"remove": CppFeatureDetail(
    name="std::remove",
    version="C++98",
    description="Removes elements equal to a specified value from a range by moving others forward",
    member_functions={
        "Signature": [
            MemberFunction("remove(first, last, value)", "Removes elements equal to value using operator==", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Value type must be EqualityComparable with T",
        "Does not erase elements from container; use erase-remove idiom to actually remove",
        "Returns iterator to new logical end of range",
    ]
),

"remove_if": CppFeatureDetail(
    name="std::remove_if",
    version="C++98",
    description="Remove elements from range that satisfy a predicate",
    member_functions={
        "Signature": [
            MemberFunction("remove_if(first, last, pred)", "Removes elements for which pred evaluates to true, returns new end iterator", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Value type must be CopyAssignable (C++98) or MoveAssignable (C++11+)",
        "UnaryPredicate must be callable with the value type",
        "Does not resize container; use erase-remove idiom to actually erase",
    ]
),

"remove_copy": CppFeatureDetail(
    name="std::remove_copy",
    version="C++98",
    description="Copies elements from a source range to a destination range, excluding those equal to a given value",
    member_functions={
        "Signature": [
            MemberFunction("remove_copy(first, last, result, value)", "Copies elements != value from [first, last) to [result, ?)", "O(n)"),
        ],
    },
    notes=[
        "InputIterator for first and last; OutputIterator for result",
        "value_type of InputIterator must be EqualityComparable with the type of value",
        "Source and destination ranges must not overlap",
        "Returns the new end iterator in the destination range",
    ]
),

"remove_copy_if": CppFeatureDetail(
    name="std::remove_copy_if",
    version="C++98",
    description="Copies elements from input range to output range, excluding those satisfying a predicate",
    member_functions={
        "Signature": [
            MemberFunction("remove_copy_if(first, last, result, pred)", "Copies elements not satisfying pred to result; returns new output iterator past last copied element", "O(last - first)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for result",
        "UnaryPredicate must be callable with value_type of InputIterator and return convertible to bool",
        "Elements must be CopyConstructible for output",
        "Does not modify source range",
    ]
),

"replace": CppFeatureDetail(
    name="std::replace",
    version="C++98",
    description="Replace all elements equal to old_value with new_value in the range",
    member_functions={
        "Signature": [
            MemberFunction("replace(first, last, old_value, new_value)", "Replace occurrences of old_value with new_value using operator==", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Elements must be EqualityComparable and Assignable",
        "Modifies the range in place",
    ]
),

"replace_if": CppFeatureDetail(
    name="std::replace_if",
    version="C++98",
    description="Replaces elements in a range that satisfy a predicate with a new value",
    member_functions={
        "Signature": [
            MemberFunction("replace_if(first, last, pred, new_value)", "Replaces elements where pred returns true with new_value", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "UnaryPredicate must be callable with value_type and return bool-convertible",
        "new_value must be assignable to value_type",
        "Modifies elements in place",
    ]
),

"replace_copy": CppFeatureDetail(
    name="std::replace_copy",
    version="C++98",
    description="Copies a range, replacing occurrences of a value with another value",
    member_functions={
        "Signature": [
            MemberFunction("replace_copy(first, last, d_first, old_value, new_value)", "Copies [first,last) to d_first, replacing old_value with new_value using operator==", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator for [first,last), OutputIterator for d_first",
        "Value types must be equality comparable with T via ==",
        "Does not modify the source range",
    ]
),

"replace_copy_if": CppFeatureDetail(
    name="std::replace_copy_if",
    version="C++98",
    description="Copies a range, replacing elements that satisfy a predicate with a new value",
    member_functions={
        "Signature": [
            MemberFunction("replace_copy_if(first, last, result, pred, old_value)", "Copies from [first, last) to result, replacing elements where pred is true with old_value", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for first and last, OutputIterator for result",
        "UnaryPredicate must accept value_type of InputIterator and return bool",
        "old_value must be assignable to value_type of OutputIterator",
        "Non-modifying sequence operation",
    ]
),

"swap": CppFeatureDetail(
    name="std::swap",
    version="C++98",
    description="Exchanges the values of two objects",
    member_functions={
        "Signature": [
            MemberFunction("template <class T> void swap(T& a, T& b)", "Swaps contents of a and b using operator= or moves if possible", "O(1)"),
            MemberFunction("template <class T1, class T2> void swap(std::pair<T1, T2>& x, std::pair<T1, T2>& y)", "Specialized swap for std::pair", "O(1)"),
        ],
    },
    notes=[
        "Requires Swappable types (noexcept-Swappable since C++17)",
        "No iterator requirements",
        "Uses std::move for efficiency if T is movable (C++11+)",
        "noexcept since C++11",
    ]
),

"swap_ranges": CppFeatureDetail(
    name="std::swap_ranges",
    version="C++98",
    description="Swaps elements between two ranges of equal length",
    member_functions={
        "Signature": [
            MemberFunction("swap_ranges(first1, last1, first2)", "Swaps elements in [first1, last1) with those starting at first2", "O(n) where n = distance(first1, last1)"),
        ],
    },
    notes=[
        "Requires ForwardIterator for all parameters",
        "Elements must be Swappable (via std::swap)",
        "Ranges must not overlap; behavior is undefined if they do",
        "Returns ForwardIterator2 to the end of the second range",
    ]
),

"iter_swap": CppFeatureDetail(
    name="std::iter_swap",
    version="C++98",
    description="Swaps the values pointed to by two forward iterators",
    member_functions={
        "Signature": [
            MemberFunction("iter_swap(ForwardIterator1 a, ForwardIterator2 b)", "Swaps *a and *b using std::swap", "O(1)"),
        ],
    },
    notes=[
        "Requires ForwardIterator1 and ForwardIterator2",
        "Value types must model Swappable (std::swap(*a, *b) must be valid)",
        "Does not modify the iterators themselves",
    ]
),

"reverse": CppFeatureDetail(
    name="std::reverse",
    version="C++98",
    description="Reverses the order of elements in the range [first, last)",
    member_functions={
        "Signature": [
            MemberFunction("reverse(first, last)", "Reverses elements by swapping", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: BidirectionalIterator",
        "Element requirement: Swappable",
        "Performs exactly (last - first)/2 swaps",
    ]
),

"reverse_copy": CppFeatureDetail(
    name="std::reverse_copy",
    version="C++98",
    description="Copies elements from a range to another range in reverse order",
    member_functions={
        "Signature": [
            MemberFunction("reverse_copy(first, last, result)", "Copies [first, last) to result in reverse order", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for result",
        "Value types must be CopyConstructible",
        "Returns OutputIterator to one past the last element written",
        "Input and output ranges may overlap if valid for iterators",
    ]
),

"rotate": CppFeatureDetail(
    name="std::rotate",
    version="C++98",
    description="Rotate elements in the range [first, last) so that the element at middle becomes the new first element",
    member_functions={
        "Signature": [
            MemberFunction("rotate(first, middle, last)", "Performs left rotation with middle as the new beginning", "O(last - first)"),
        ],
    },
    notes=[
        "Requires BidirectionalIterator",
        "Value type must be CopyAssignable",
        "The behavior is undefined if first == middle or middle == last",
    ]
),

"rotate_copy": CppFeatureDetail(
    name="std::rotate_copy",
    version="C++98",
    description="Copies a rotated range [first, last) to a destination starting at d_first",
    member_functions={
        "Signature": [
            MemberFunction("rotate_copy(first, middle, last, d_first)", "Copies elements rotated so middle becomes first in output", "O(N)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator for first, middle, last; OutputIterator for d_first",
        "middle must be a valid iterator in [first, last)",
        "Source range is unchanged; destination must accommodate N elements where N = last - first",
    ]
),

"shuffle": CppFeatureDetail(
    name="std::shuffle",
    version="C++11",
    description="Randomly shuffles elements in the range using a uniform random bit generator",
    member_functions={
        "Signature": [
            MemberFunction("shuffle(first, last, g)", "Shuffles [first, last) using generator g", "Average O(n)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Value types must be Swappable",
        "g must be a UniformRandomBitGenerator",
    ]
),

"sample": CppFeatureDetail(
    name="std::sample",
    version="C++17",
    description="Selects a random sample of n elements from the range [first, last) and stores them starting at out",
    member_functions={
        "Signature": [
            MemberFunction("sample(first, last, out, n, g)", "Sample using provided random number generator g", "O(min(n, last-first))"),
            MemberFunction("sample(first, last, out, n)", "Sample using default random number generator", "O(min(n, last-first))"),
        ],
    },
    notes=[
        "Requires ForwardIterator for [first, last)",
        "Requires OutputIterator for out",
        "Undefined behavior if n > (last - first)",
        "Value type of input iterators must be CopyInsertable or MoveInsertable into output",
        "Sampling is uniform without replacement",
    ]
),

"unique": CppFeatureDetail(
    name="std::unique",
    version="C++98",
    description="Removes consecutive duplicate elements from a range",
    member_functions={
        "Signature": [
            MemberFunction("unique(first, last)", "Remove consecutive duplicates using operator==", "O(n)"),
            MemberFunction("unique(first, last, pred)", "Remove consecutive duplicates using binary predicate", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Elements must be EqualityComparable (default overload) and CopyAssignable",
        "Only removes consecutive duplicates; range should be sorted first to remove all duplicates",
        "Returns iterator to new logical end of unique range",
        "Elements beyond new end remain but in unspecified order",
    ]
),

"unique_copy": CppFeatureDetail(
    name="std::unique_copy",
    version="C++98",
    description="Copies elements from a range to an output range, omitting consecutive duplicates",
    member_functions={
        "Signature": [
            MemberFunction("unique_copy(first, last, d_first)", "Copies using operator== to determine equality", "O(n)"),
            MemberFunction("unique_copy(first, last, d_first, pred)", "Copies using binary predicate to determine equality", "O(n)"),
        ],
    },
    notes=[
        "InputIterator for input range, OutputIterator for output range",
        "Elements must be equality comparable via == or the provided predicate",
        "Only removes consecutive duplicates; input should be sorted first to remove all duplicates",
    ]
),

"partition": CppFeatureDetail(
    name="std::partition",
    version="C++98",
    description="Rearranges elements so that those satisfying the predicate come before those that do not",
    member_functions={
        "Signature": [
            MemberFunction("partition(first, last, pred)", "Rearranges range [first, last) using predicate pred", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Element requirement: MoveAssignable (CopyAssignable in C++98)",
        "Not stable; relative order of elements is not preserved",
        "Returns iterator to the first element not satisfying pred",
    ]
),

"stable_partition": CppFeatureDetail(
    name="std::stable_partition",
    version="C++98",
    description="Stable partition of elements based on a predicate",
    member_functions={
        "Signature": [
            MemberFunction("stable_partition(first, last, pred)", "Rearranges elements so those satisfying pred come first, preserving relative order", "O(N log N) worst case, O(N) if extra memory available"),
        ],
    },
    notes=[
        "Requires BidirectionalIterator",
        "Elements must be MoveAssignable (C++11) or CopyAssignable",
        "Predicate must not invalidate iterators or references",
        "Stable: preserves relative order within each partition",
    ]
),

"partition_copy": CppFeatureDetail(
    name="std::partition_copy",
    version="C++11",
    description="Copies elements from a range to two separate output ranges based on a predicate",
    member_functions={
        "Signature": [
            MemberFunction("partition_copy(first, last, out_true, out_false, p)", "Copies elements where p returns true to out_true and false to out_false", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last), OutputIterator for out_true and out_false",
        "UnaryPredicate p must be callable with the value type of InputIterator",
        "Output ranges must not overlap with input range",
    ]
),

"is_partitioned": CppFeatureDetail(
    name="std::is_partitioned",
    version="C++11",
    description="Checks if the range is partitioned such that all elements satisfying the predicate come before those that do not",
    member_functions={
        "Signature": [
            MemberFunction("is_partitioned(first, last, pred)", "Tests partition using the unary predicate pred", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator",
        "UnaryPredicate must be callable with the value type of the iterator",
        "Returns true if the range is partitioned, false otherwise",
    ]
),

"partition_point": CppFeatureDetail(
    name="std::partition_point",
    version="C++20",
    description="Returns the first iterator in the partitioned range not satisfying the predicate",
    member_functions={
        "Signature": [
            MemberFunction("partition_point(first, last, pred)", "Finds partition point using unary predicate", "O(log (last-first)) if RandomAccessIterator, otherwise O(last-first)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "UnaryPredicate must be callable with ForwardIterator::value_type",
        "Assumes [first, last) is partitioned: all elements before the point satisfy pred, after do not",
    ]
),

"sort": CppFeatureDetail(
    name="std::sort",
    version="C++98",
    description="Sorts the elements in the range [first, last) into ascending order",
    member_functions={
        "Signature": [
            MemberFunction("void sort(RandomAccessIterator first, RandomAccessIterator last)", "Sorts using operator<", "Average O(N log N) comparisons, worst O(N log N)"),
            MemberFunction("void sort(RandomAccessIterator first, RandomAccessIterator last, Compare comp)", "Sorts using the given comparator", "Average O(N log N) comparisons, worst O(N log N)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "For the first overload, value type must be LessThanComparable (operator< defined); for the second, Compare must impose strict weak ordering",
        "Elements must be MoveAssignable (C++11); otherwise CopyAssignable",
        "Not stable; may rearrange equal elements",
        "Undefined behavior if initial order does not satisfy the comparator",
    ]
),

"stable_sort": CppFeatureDetail(
    name="std::stable_sort",
    version="C++98",
    description="Sorts elements in ascending order while preserving relative order of equal elements",
    member_functions={
        "Signature": [
            MemberFunction("stable_sort(first, last)", "Sort using operator<", "O(n log n)"),
            MemberFunction("stable_sort(first, last, comp)", "Sort with custom comparator", "O(n log n)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "ValueSwappable and LessThanComparable (or provided comparator imposes strict weak ordering)",
        "Stable sorting algorithm",
    ]
),

"partial_sort": CppFeatureDetail(
    name="std::partial_sort",
    version="C++98",
    description="Partially sorts elements in a range up to a specified iterator",
    member_functions={
        "Signature": [
            MemberFunction("partial_sort(first, middle, last)", "Partially sort using operator<", "O(n log m) average, O(n log n) worst case"),
            MemberFunction("partial_sort(first, middle, last, comp)", "Partially sort with custom comparator", "O(n log m) average, O(n log n) worst case"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Value type must be MoveAssignable (C++11); LessThanComparable or compatible with comp",
        "After call, [first, middle) is sorted; for i in [middle, last), !comp(*middle, *i)",
        "Not stable",
    ]
),

"partial_sort_copy": CppFeatureDetail(
    name="std::partial_sort_copy",
    version="C++98",
    description="Copies the smallest elements from source range to destination and sorts them",
    member_functions={
        "Signature": [
            MemberFunction("partial_sort_copy(first, last, result_first, result_last)", "Copy and partially sort using operator<", "O(N log M)"),
            MemberFunction("partial_sort_copy(first, last, result_first, result_last, comp)", "Copy and partially sort with custom comparator", "O(N log M)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last)",
        "Requires RandomAccessIterator for [result_first, result_last)",
        "Value types must be LessThanComparable or compatible with comp",
        "N = last - first, M = result_last - result_first; copies min(N, M) elements",
        "Returns iterator to the end of the copied range in destination",
    ]
),

"is_sorted": CppFeatureDetail(
    name="std::is_sorted",
    version="C++11",
    description="Checks if the elements in the range are sorted in non-descending order",
    member_functions={
        "Signature": [
            MemberFunction("is_sorted(first, last)", "Checks if sorted using operator<", "O(n)"),
            MemberFunction("is_sorted(first, last, comp)", "Checks if sorted using comp", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Elements must be LessThanComparable for default overload",
        "Returns true for empty or single-element ranges",
    ]
),

"is_sorted_until": CppFeatureDetail(
    name="std::is_sorted_until",
    version="C++11",
    description="Returns iterator to first unsorted element in range",
    member_functions={
        "Signature": [
            MemberFunction("is_sorted_until(first, last)", "Checks using operator<", "O(n)"),
            MemberFunction("is_sorted_until(first, last, comp)", "Checks with custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Elements must be LessThanComparable for default overload",
        "Returns last if entire range is sorted",
    ]
),

"nth_element": CppFeatureDetail(
    name="std::nth_element",
    version="C++98",
    description="Rearranges elements in [first, last) so that the element at nth is in its sorted position",
    member_functions={
        "Signature": [
            MemberFunction("nth_element(first, nth, last)", "Uses operator< for comparisons", "Average O(n), worst O(n^2)"),
            MemberFunction("nth_element(first, nth, last, comp)", "Uses custom comparator comp", "Average O(n), worst O(n^2)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Elements must be MoveAssignable; for operator< overload, LessThanComparable",
        "The comparator comp must induce a strict weak ordering",
        "Elements before nth are not greater than *nth; elements after are not less than *nth",
    ]
),

"binary_search": CppFeatureDetail(
    name="std::binary_search",
    version="C++98",
    description="Determine if an element exists in a sorted range using binary search",
    member_functions={
        "Signature": [
            MemberFunction("binary_search(first, last, value)", "Searches for value using operator<", "O(log n) comparisons"),
            MemberFunction("binary_search(first, last, value, comp)", "Searches for value using custom comparator comp", "O(log n) comparisons"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Element requirement: Value type must be LessThanComparable with operator< or compatible with comp",
        "Range [first, last) must be sorted in ascending order; behavior is undefined otherwise",
        "Returns true if value is present at least once, false otherwise",
    ]
),

"lower_bound": CppFeatureDetail(
    name="std::lower_bound",
    version="C++98",
    description="Returns iterator to first element not less than value in sorted range",
    member_functions={
        "Signature": [
            MemberFunction("lower_bound(first, last, value)", "Binary search using operator<", "O(log N) comparisons"),
            MemberFunction("lower_bound(first, last, value, comp)", "Binary search with custom comparator", "O(log N) comparisons"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Element requirement: Value type comparable to elements via < or comp",
        "Requires [first, last) to be sorted in non-decreasing order",
        "Logarithmic complexity assumes RandomAccessIterator; otherwise O(N)",
    ]
),

"upper_bound": CppFeatureDetail(
    name="std::upper_bound",
    version="C++98",
    description="Returns iterator to first element greater than value in sorted range",
    member_functions={
        "Signature": [
            MemberFunction("upper_bound(first, last, value)", "Finds insertion point using operator<", "O(log n) comparisons"),
            MemberFunction("upper_bound(first, last, value, comp)", "Finds insertion point using comparator comp", "O(log n) comparisons"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Range [first, last) must be sorted in non-decreasing order w.r.t. value (or comp)",
        "Elements and value must support LessThanComparable (via operator< or comp)",
        "Returns last() if value is greater than or equal to all elements",
        "Logarithmic time requires RandomAccessIterator; ForwardIterator yields linear time",
    ]
),

"equal_range": CppFeatureDetail(
    name="std::equal_range",
    version="C++98",
    description="Returns the range of elements equal to a specified value in a sorted range",
    member_functions={
        "Signature": [
            MemberFunction("equal_range(first, last, val)", "Finds equal range using operator<", "O(log n)"),
            MemberFunction("equal_range(first, last, val, comp)", "Finds equal range using custom comparator", "O(log n)"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Element requirement: LessThanComparable between iterator value_type and val (or via comp)",
        "Range [first, last) must be sorted with respect to val or comp",
        "Returns pair of iterators: lower_bound to upper_bound",
        "Linear if ForwardIterator; logarithmic if RandomAccessIterator",
    ]
),

"merge": CppFeatureDetail(
    name="std::merge",
    version="C++98",
    description="Merges two sorted ranges into a single sorted output range",
    member_functions={
        "Signature": [
            MemberFunction("merge(first1, last1, first2, last2, result)", "Merges using operator<", "O(n)"),
            MemberFunction("merge(first1, last1, first2, last2, result, comp)", "Merges with custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for input ranges and OutputIterator for output",
        "Input ranges must be sorted in non-descending order (or according to comp)",
        "Elements must be LessThanComparable (via operator< or comp)",
        "Undefined behavior if output range overlaps with input ranges",
    ]
),

"inplace_merge": CppFeatureDetail(
    name="std::inplace_merge",
    version="C++98",
    description="Merges two consecutive sorted ranges into a single sorted range in place",
    member_functions={
        "Signature": [
            MemberFunction("inplace_merge(first, middle, last)", "Merges using operator<", "O(N log N) worst case, linear if extra memory available"),
            MemberFunction("inplace_merge(first, middle, last, comp)", "Merges with custom comparator", "O(N log N) worst case, linear if extra memory available"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Ranges [first, middle) and [middle, last) must both be sorted",
        "Elements must be CopyAssignable (or MoveAssignable in C++11+)",
        "Throws if comp throws or if temporary buffer allocation fails",
    ]
),

"includes": CppFeatureDetail(
    name="std::includes",
    version="C++98",
    description="Checks if a sorted range is a subsequence of another sorted range",
    member_functions={
        "Signature": [
            MemberFunction("includes(InputIterator1 first1, InputIterator1 last1, InputIterator2 first2, InputIterator2 last2)", "Checks inclusion using operator==", "O((last1 - first1) + (last2 - first2))"),
            MemberFunction("includes(InputIterator1 first1, InputIterator1 last1, InputIterator2 first2, InputIterator2 last2, BinaryPredicate pred)", "Checks inclusion using custom predicate", "O((last1 - first1) + (last2 - first2))"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator for both ranges",
        "Element requirement: EqualityComparable (via operator== or pred)",
        "Both ranges must be sorted in non-decreasing order",
        "Returns true if every element in [first2, last2) appears in [first1, last1) in order",
    ]
),

"set_difference": CppFeatureDetail(
    name="std::set_difference",
    version="C++98",
    description="Constructs a sorted range with elements present in the first range but not the second",
    member_functions={
        "Signature": [
            MemberFunction("set_difference(first1, last1, first2, last2, result)", "Difference using operator<", "O(N + M)"),
            MemberFunction("set_difference(first1, last1, first2, last2, result, comp)", "Difference with custom comparator", "O(N + M)"),
        ],
    },
    notes=[
        "Requires InputIterator for input ranges and OutputIterator for output",
        "Both input ranges must be sorted in ascending order",
        "Elements must be LessThanComparable via operator< or comp",
        "Returns iterator to the end of the output range",
    ]
),

"set_intersection": CppFeatureDetail(
    name="std::set_intersection",
    version="C++98",
    description="Computes the intersection of two sorted ranges and stores the result in an output range",
    member_functions={
        "Signature": [
            MemberFunction("set_intersection(first1, last1, first2, last2, result)", "Computes intersection using operator<", "O(n + m) comparisons"),
            MemberFunction("set_intersection(first1, last1, first2, last2, result, comp)", "Computes intersection using custom comparator", "O(n + m) comparisons"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator for input ranges, OutputIterator for result",
        "Element requirement: LessThanComparable (via operator< or comp)",
        "Both input ranges must be sorted in ascending order",
        "Returns the end of the output range; undefined behavior if output range is too small",
    ]
),

"set_symmetric_difference": CppFeatureDetail(
    name="std::set_symmetric_difference",
    version="C++98",
    description="Computes the symmetric difference of two sorted ranges into a third range",
    member_functions={
        "Signature": [
            MemberFunction("set_symmetric_difference(first1, last1, first2, last2, d_first)", "Symmetric difference using operator<", "O(N + M)"),
            MemberFunction("set_symmetric_difference(first1, last1, first2, last2, d_first, comp)", "Symmetric difference with custom comparator", "O(N + M)"),
        ],
    },
    notes=[
        "Requires InputIterator for input ranges (must be sorted in ascending order)",
        "Requires OutputIterator for output range",
        "Elements must be LessThanComparable (or comparable via comp)",
        "Returns iterator to the end of the output range",
        "Undefined behavior if input ranges are not sorted",
    ]
),

"set_union": CppFeatureDetail(
    name="std::set_union",
    version="C++98",
    description="Computes the union of two sorted input ranges into an output range",
    member_functions={
        "Signature": [
            MemberFunction("set_union(first1, last1, first2, last2, d_first)", "Union using operator<", "O(N + M)"),
            MemberFunction("set_union(first1, last1, first2, last2, d_first, comp)", "Union with custom comparator", "O(N + M)"),
        ],
    },
    notes=[
        "Requires InputIterator for input ranges and OutputIterator for output",
        "Both input ranges must be sorted in ascending order",
        "Elements must be CopyAssignable; comparator (if used) must impose strict weak ordering",
        "Duplicates are removed; output may require up to N + M elements",
    ]
),

"make_heap": CppFeatureDetail(
    name="std::make_heap",
    version="C++98",
    description="Constructs a max-heap from the range [first, last)",
    member_functions={
        "Signature": [
            MemberFunction("make_heap(first, last)", "Builds max-heap using operator<", "O(n)"),
            MemberFunction("make_heap(first, last, comp)", "Builds max-heap using comparator comp", "O(n)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "ValueType must be LessThanComparable for operator< overload; comp must induce strict weak ordering",
        "Largest element is placed at first after construction",
    ]
),

"push_heap": CppFeatureDetail(
    name="std::push_heap",
    version="C++98",
    description="Moves the new element at the end of a heap range into its correct position",
    member_functions={
        "Signature": [
            MemberFunction("push_heap(first, last)", "Pushes using operator<", "O(log (last - first))"),
            MemberFunction("push_heap(first, last, comp)", "Pushes using custom comparator", "O(log (last - first))"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "The range [first, last-1) must form a valid heap before the call",
        "ValueType must be LessThanComparable for operator< overload; otherwise, comparable via comp",
        "Elements must be MoveAssignable",
    ]
),

"pop_heap": CppFeatureDetail(
    name="std::pop_heap",
    version="C++98",
    description="Removes the largest element from the front of a heap and restores the heap property",
    member_functions={
        "Signature": [
            MemberFunction("pop_heap(first, last)", "Pops the root using operator<", "O(log n)"),
            MemberFunction("pop_heap(first, last, comp)", "Pops the root using custom comparator", "O(log n)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Elements must be MoveAssignable (CopyAssignable pre-C++11)",
        "The range [first, last) must form a valid max-heap before the call",
        "After the call, the popped element is at *(last-1), and [first, last-1) is a heap",
    ]
),

"sort_heap": CppFeatureDetail(
    name="std::sort_heap",
    version="C++98",
    description="Sorts the elements in a heap range into ascending order",
    member_functions={
        "Signature": [
            MemberFunction("sort_heap(first, last)", "Sorts heap using operator<", "O(n log n) comparisons"),
            MemberFunction("sort_heap(first, last, comp)", "Sorts heap using custom comparator", "O(n log n) comparisons"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Range [first, last) must form a valid heap before sorting",
        "Elements must be LessThanComparable (for default) or compatible with comp",
        "Results in sorted order; destroys heap property",
    ]
),

"is_heap": CppFeatureDetail(
    name="std::is_heap",
    version="C++11",
    description="Checks if the range forms a heap",
    member_functions={
        "Signature": [
            MemberFunction("is_heap(first, last)", "Checks using operator<", "O(n)"),
            MemberFunction("is_heap(first, last, comp)", "Checks with custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Compare must induce strict weak ordering",
        "Performs at most (last - first) comparisons",
    ]
),

"is_heap_until": CppFeatureDetail(
    name="std::is_heap_until",
    version="C++11",
    description="Returns the first iterator where the heap property fails in the range",
    member_functions={
        "Signature": [
            MemberFunction("is_heap_until(first, last)", "Checks heap property using operator<", "O(n)"),
            MemberFunction("is_heap_until(first, last, comp)", "Checks heap property using custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Requires RandomAccessIterator",
        "Elements must be LessThanComparable for default overload",
        "Returns last if the entire range satisfies the heap property"
    ]
),

"min": CppFeatureDetail(
    name="std::min",
    version="C++98",
    description="Returns the smaller of two values",
    member_functions={
        "Signature": [
            MemberFunction("min(const T& a, const T& b)", "Returns the smaller value using operator<", "O(1)"),
            MemberFunction("min(std::initializer_list<T> ilist)", "Returns the smallest value in the initializer list using operator<", "O(n)"),
            MemberFunction("min(const T& a, const T& b, Compare comp)", "Returns the smaller value using custom comparator", "O(1)"),
            MemberFunction("min(std::initializer_list<T> ilist, Compare comp)", "Returns the smallest value in the initializer list using custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Requires LessThanComparable for operator< overloads (types with defined operator<)",
        "Comparator must impose strict weak ordering",
        "C++11: Added constexpr and initializer_list overloads",
        "No iterator requirements as it operates on individual elements or lists",
    ]
),

"max": CppFeatureDetail(
    name="std::max",
    version="C++98",
    description="Returns the greater of two values or the maximum in an initializer list",
    member_functions={
        "Signature": [
            MemberFunction("max(const T& a, const T& b)", "Returns the larger of a and b using operator<", "O(1)"),
            MemberFunction("max(const T& a, const T& b, Compare comp)", "Returns the larger of a and b using comp", "O(1)"),
            MemberFunction("max(std::initializer_list<T> ilist)", "Returns the maximum value in ilist using operator<", "O(n)"),
            MemberFunction("max(std::initializer_list<T> ilist, Compare comp)", "Returns the maximum value in ilist using comp", "O(n)"),
        ],
    },
    notes=[
        "Requires T to be LessThanComparable via operator< or the provided comp",
        "Constexpr since C++11",
        "Initializer list overloads available since C++11",
        "Undefined behavior if ilist is empty",
    ]
),

"minmax": CppFeatureDetail(
    name="std::minmax",
    version="C++11",
    description="Returns the smaller and larger of two values as a pair",
    member_functions={
        "Signature": [
            MemberFunction("minmax(const T& a, const T& b)", "Default comparator using operator<", "O(1)"),
            MemberFunction("minmax(const T& a, const T& b, Compare comp)", "Custom comparator", "O(1)"),
            MemberFunction("minmax(InitIL first, InitIL last)", "For initializer_list with default comparator", "O(1)"),
            MemberFunction("minmax(InitIL first, InitIL last, Compare comp)", "For initializer_list with custom comparator", "O(1)"),
        ],
    },
    notes=[
        "T must be LessThanComparable (for default) or compatible with comp",
        "Returns pair<const T&, const T&> with first <= second",
        "Throws if comp throws",
    ]
),

"min_element": CppFeatureDetail(
    name="std::min_element",
    version="C++98",
    description="Finds the smallest element in a range",
    member_functions={
        "Signature": [
            MemberFunction("min_element(first, last)", "Finds minimum using operator<", "O(n)"),
            MemberFunction("min_element(first, last, comp)", "Finds minimum using custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Requires ForwardIterator",
        "Value type must support LessThanComparable for operator< overload",
        "Returns last() if range is empty; returns first occurrence if multiple minima",
    ]
),

"max_element": CppFeatureDetail(
    name="std::max_element",
    version="C++98",
    description="Finds the largest element in a range",
    member_functions={
        "Signature": [
            MemberFunction("max_element(first, last)", "Finds maximum using operator<", "O(n)"),
            MemberFunction("max_element(first, last, comp)", "Finds maximum using custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Elements must be LessThanComparable via operator< or the provided comparator",
        "Returns last if the range is empty",
        "If multiple maximum elements exist, returns iterator to the first one",
    ]
),

"minmax_element": CppFeatureDetail(
    name="std::minmax_element",
    version="C++11",
    description="Finds the minimum and maximum elements in a range",
    member_functions={
        "Signature": [
            MemberFunction("minmax_element(first, last)", "Finds min and max using operator<", "O(n)"),
            MemberFunction("minmax_element(first, last, comp)", "Finds min and max using custom comparator", "O(n)"),
        ],
    },
    notes=[
        "Iterator requirement: ForwardIterator",
        "Elements must be LessThanComparable with the comparator (defaults to operator<)",
        "Returns pair of iterators to first min and first max; for <2 elements, both point to the single element or end",
    ]
),

"clamp": CppFeatureDetail(
    name="std::clamp",
    version="C++17",
    description="Clamp a value between lower and upper bounds",
    member_functions={
        "Signature": [
            MemberFunction("constexpr const T& clamp(const T& v, const T& lo, const T& hi)", "Clamp using operator<", "O(1)"),
            MemberFunction("constexpr const T& clamp(const T& v, const T& lo, const T& hi, Compare comp)", "Clamp with custom comparator", "O(1)"),
        ],
    },
    notes=[
        "No iterator requirements",
        "T must be LessThanComparable (via operator< or comp)",
        "Returns lo if v < lo, hi if v > hi, otherwise v",
    ]
),

"equal": CppFeatureDetail(
    name="std::equal",
    version="C++98",
    description="Checks if two ranges are equal element-wise",
    member_functions={
        "Signature": [
            MemberFunction("equal(first1, last1, first2)", "Compares elements using operator==", "O(n)"),
            MemberFunction("equal(first1, last1, first2, pred)", "Compares elements using binary predicate", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for both ranges",
        "Value types must be EqualityComparable for first overload; BinaryPredicate for second",
        "Second range must be at least as long as first, or behavior is undefined",
    ]
),

"lexicographical_compare": CppFeatureDetail(
    name="std::lexicographical_compare",
    version="C++98",
    description="Performs lexicographical comparison between two ranges",
    member_functions={
        "Signature": [
            MemberFunction("lexicographical_compare(first1, last1, first2, last2)", "Compares using operator<", "O(min((last1-first1), (last2-first2)))"),
            MemberFunction("lexicographical_compare(first1, last1, first2, last2, comp)", "Compares using custom binary predicate", "O(min((last1-first1), (last2-first2)))"),
        ],
    },
    notes=[
        "Requires InputIterator for both ranges",
        "Elements must be LessThanComparable via operator< or the provided comp",
        "Returns true if the first range is lexicographically less than the second",
    ]
),

"accumulate": CppFeatureDetail(
    name="std::accumulate",
    version="C++98",
    description="Computes the sum of elements in a range using addition or a binary operation",
    member_functions={
        "Signature": [
            MemberFunction("accumulate(first, last, init)", "Accumulates using operator+ starting from init", "O(n)"),
            MemberFunction("accumulate(first, last, init, op)", "Accumulates using custom binary operation op starting from init", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for first and last",
        "Value types must support the binary operation (operator+ by default); init must be compatible",
        "Accumulation performed left-to-right; undefined behavior if op is not associative",
    ]
),

"reduce": CppFeatureDetail(
    name="std::reduce",
    version="C++17",
    description="Computes the reduction of a range using a binary operation",
    member_functions={
        "Signature": [
            MemberFunction("reduce(first, last, init)", "Sequential reduction with default addition", "O(n)"),
            MemberFunction("reduce(policy, first, last, init)", "Parallel reduction with default addition", "O(n)"),
            MemberFunction("reduce(first, last, init, op)", "Sequential reduction with custom binary operation", "O(n)"),
            MemberFunction("reduce(policy, first, last, init, op)", "Parallel reduction with custom binary operation", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for first and last",
        "Value type must support the binary operation; default is std::plus<>{}",
        "Order of operations unspecified; must be associative for parallel correctness",
        "Defined in <numeric>",
    ]
),

"transform_reduce": CppFeatureDetail(
    name="std::transform_reduce",
    version="C++17",
    description="Transforms elements and computes their reduction",
    member_functions={
        "Signature": [
            MemberFunction("transform_reduce(first, last, init, binary_op, unary_op)", "Applies unary_op to each element in [first, last) and reduces results using binary_op starting from init", "O(last - first)"),
            MemberFunction("transform_reduce(first1, last1, first2, init, binary_op, binary_transform_op)", "Applies binary_transform_op to pairs from [first1, last1) and starting at first2, then reduces using binary_op starting from init", "O(last1 - first1)"),
            MemberFunction("transform_reduce(policy, first, last, init, binary_op, unary_op)", "Parallel version of single-range overload", "O(last - first)"),
            MemberFunction("transform_reduce(policy, first1, last1, first2, init, binary_op, binary_transform_op)", "Parallel version of two-range overload", "O(last1 - first1)"),
        ],
    },
    notes=[
        "Iterator requirement: InputIterator for all ranges",
        "binary_op must accept two arguments of type T (or convertible) and return T",
        "For parallel execution policies, binary_op and transform operations must be associative and commutative",
        "Defined in <numeric>",
    ]
),

"exclusive_scan": CppFeatureDetail(
    name="std::exclusive_scan",
    version="C++17",
    description="Computes the exclusive prefix scan of a range using a binary operation",
    member_functions={
        "Signature": [
            MemberFunction("exclusive_scan(first, last, d_first, init, binary_op)", "Performs exclusive scan with initializer and custom operation", "O(n)"),
            MemberFunction("exclusive_scan(first, last, d_first, init)", "Performs exclusive scan with initializer using operator+", "O(n)"),
            MemberFunction("exclusive_scan(first, last, d_first, binary_op)", "Performs exclusive scan using first element as initializer and custom operation", "O(n)"),
            MemberFunction("exclusive_scan(exec, first, last, d_first, init, binary_op)", "Parallel version with execution policy", "O(n)"),
            MemberFunction("exclusive_scan(exec, first, last, d_first, init)", "Parallel version with execution policy using operator+", "O(n)"),
            MemberFunction("exclusive_scan(exec, first, last, d_first, binary_op)", "Parallel version with execution policy using first element as initializer", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for [d_first, d_first + (last - first))",
        "binary_op must be a binary function compatible with the value type",
        "The output at d_first + i is the result of applying binary_op to the previous result and input[i-1] (exclusive)",
        "Overloads with execution policy require <execution> header",
    ]
),

"inclusive_scan": CppFeatureDetail(
    name="std::inclusive_scan",
    version="C++17",
    description="Computes inclusive prefix sums over the range [first, last)",
    member_functions={
        "Signature": [
            MemberFunction("inclusive_scan(first, last, d_first)", "Accumulates using operator+", "O(n)"),
            MemberFunction("inclusive_scan(first, last, d_first, binary_op)", "Accumulates using custom binary_op", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for [d_first, d_first + (last - first))",
        "The type of elements must support the binary operation (default: std::plus<>)",
        "Input and output ranges shall not overlap unless d_first == first and InputIterator == OutputIterator",
    ]
),

"transform_exclusive_scan": CppFeatureDetail(
    name="std::transform_exclusive_scan",
    version="C++17",
    description="Applies unary transformation followed by exclusive prefix scan on a range",
    member_functions={
        "Signature": [
            MemberFunction("transform_exclusive_scan(first, last, d_first, init, binary_op, unary_op)", "Transforms input elements with unary_op then exclusive scans with binary_op starting from init", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for output",
        "binary_op: T, T -> T; unary_op: InputIt::value_type -> T",
        "Output range must be at least as long as input; no overlap with input",
        "Returns OutputIt one past the last output element",
    ]
),

"transform_inclusive_scan": CppFeatureDetail(
    name="std::transform_inclusive_scan",
    version="C++17",
    description="Applies unary operation to elements and computes inclusive prefix sums with binary operation",
    member_functions={
        "Signature": [
            MemberFunction("transform_inclusive_scan(first, last, d_first, unary_op, init, binary_op)", "Transforms input with unary_op and accumulates inclusive scan starting from init using binary_op", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first, last) and OutputIterator for d_first",
        "T is the accumulation type; unary_op must return type compatible with binary_op(T, decltype(unary_op(*first)))",
        "To start scan with unary_op(*first), use init as identity element for binary_op (e.g., T{} for summation)",
        "Input and output ranges may overlap if input iterators are not advanced past the end of the output range",
    ]
),

"adjacent_difference": CppFeatureDetail(
    name="std::adjacent_difference",
    version="C++98",
    description="Computes the differences between adjacent elements in a range",
    member_functions={
        "Signature": [
            MemberFunction("adjacent_difference(first, last, d_first)", "Compute differences using operator-", "O(n)"),
            MemberFunction("adjacent_difference(first, last, d_first, op)", "Compute differences using binary operation op", "O(n)"),
        ],
    },
    notes=[
        "Requires InputIterator for input range [first, last)",
        "Requires OutputIterator for output range starting at d_first",
        "First input element is copied to output; subsequent outputs are differences of adjacent elements",
        "Elements must support subtraction (operator-) or the provided binary operation",
    ]
),

"inner_product": CppFeatureDetail(
    name="std::inner_product",
    version="C++98",
    description="Computes the inner product of two ranges",
    member_functions={
        "Signature": [
            MemberFunction("inner_product(first1, last1, first2, init)", "Uses operator* for multiplication and operator+ for accumulation", "O(last1 - first1)"),
            MemberFunction("inner_product(first1, last1, first2, init, binary_op)", "Uses operator* for multiplication and custom binary_op for accumulation", "O(last1 - first1)"),
        ],
    },
    notes=[
        "Requires InputIterator for [first1, last1) and first2",
        "The value type must support the required arithmetic operations",
        "Advances first2 by the same distance as [first1, last1)",
    ]
),

"gcd": CppFeatureDetail(
    name="std::gcd",
    version="C++17",
    description="Computes the greatest common divisor of two integers",
    member_functions={
        "Signature": [
            MemberFunction("gcd(m, n)", "Computes GCD using Euclidean algorithm", "O(log min(|m|, |n|))"),
        ],
    },
    notes=[
        "Requires M and N to be integer types (std::integral)",
        "Returns abs(m) if n == 0, abs(n) if m == 0, 0 if both 0",
        "Noexcept and constexpr",
    ]
),

"lcm": CppFeatureDetail(
    name="std::lcm",
    version="C++17",
    description="Computes the least common multiple of two integer values",
    member_functions={
        "Signature": [
            MemberFunction("lcm(m, n)", "Computes LCM of m and n, where m and n are integers", "O(1)"),
        ],
    },
    notes=[
        "Requires integral types M and N",
        "Returns 0 if either m or n is 0",
        "Undefined behavior if the result cannot be represented in the return type (common_type_t<M,N>)",
        "No iterator requirements",
    ]
),

