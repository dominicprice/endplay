#include <string>
#include <vector>
#include <variant>

class Node
{
public:
	enum class Type
	{
		ROOT,
		SYMBOL,
		OPERATOR,
		FUNCTION,
		ACTION,
		VALUE
	};

	Node(const std::string& value, Type dtype);
	Node(int value, Type dtype);

	void append_child(const Node& other);

	const Node& first_child() const;
	const Node& middle_child() const;
	const Node& last_child() const;
	int n_children();

	void pprint(int indent = 0) const;

	std::variant<std::string, int> value;
	Type dtype;
	std::vector<Node> children;
};
