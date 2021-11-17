#include <pybind11/pybind11.h>
#include "node.h"

namespace py = pybind11;

Node::Node(const std::string& value, Type dtype)
	: value(value), dtype(dtype) {}

Node::Node(int value, Type dtype)
	: value(value), dtype(dtype) {}

void Node::append_child(const Node& other)
{
	children.push_back(other);
}

const Node& Node::first_child() const { return children[0]; }
const Node& Node::middle_child() const { return children[1]; }
const Node& Node::last_child() const { return children.back(); }
int Node::n_children() { return static_cast<int>(children.size()); }

void Node::pprint(int indent) const
{
	std::string this_line(indent, ' ');
	this_line += "-> " + std::holds_alternative<std::string>(value)
		? std::get<std::string>(value)
		: std::to_string(std::get<int>(value));
	py::print(this_line);
	for (const auto& child : children)
		pprint(indent + 2);
}

PYBIND11_MODULE(node, m)
{
	auto PyNode = py::class_<Node>(m, "Node")
		.def(py::init<const std::string&, Node::Type>())
		.def(py::init<int, Node::Type>())
		.def("append_child", &Node::append_child)
		.def_property_readonly("first_child", &Node::first_child)
		.def_property_readonly("middle_child", &Node::middle_child)
		.def_property_readonly("last_child", &Node::last_child)
		.def("pprint", [](const Node& node) { node.pprint(0); });

	auto PyNodeType = py::enum_<Node::Type>(PyNode, "Type")
		.value("ROOT", Node::Type::ROOT)
		.value("SYMBOL", Node::Type::SYMBOL)
		.value("OPERATOR", Node::Type::OPERATOR)
		.value("FUNCTION", Node::Type::FUNCTION)
		.value("ACTION", Node::Type::ACTION)
		.value("VALUE", Node::Type::VALUE);
}