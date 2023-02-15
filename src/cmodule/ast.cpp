#include <stdexcept>

#include "ast.h"

//root node

NodePtr RootNode::create(std::vector<NodePtr>&& children)
{
  auto res = std::make_unique<RootNode>();
  res->children = std::move(children);
  return res;
}


// metadata node

Node::Type MetadataNode::type() const
{
  return Node::METADATA;
}

MetadataNode::Key MetadataNode::key() const
{
  return key_;
}

unsigned int MetadataNode::generate() const
{
  return std::get<0>(value_);
}

unsigned int MetadataNode::produce() const
{
  return std::get<0>(value_);
}

Vul MetadataNode::vul() const
{
  return std::get<1>(value_);
}

Seat MetadataNode::dealer() const
{
  return std::get<2>(value_);
}

deal MetadataNode::predeal() const
{
  return std::get<3>(value_);
}


// definition node

DefinitionNodePtr DefinitionNode::create(const std::string& name, ExpressionNodePtr&& value)
{
  auto res = std::make_unique<DefinitionNode>();
  res->name = name;
  res->value = std::move(value);
  return res;
}

Node::Type DefinitionNode::type() const
{
  return Node::DEFINITION;
}

// expression nodes

Node::Type ExpressionNode::type() const
{
  return Node::EXPRESSION;
}

NodePtr SymbolNode::create(const std::string& name)
{
  auto res = std::make_unique<SymbolNode>();
  res->name = name;
  return res;
}

ValueNodePtr SymbolNode::evaluate(const deal& dl, const Environment &env) const
{
  return env.get(name)->evaluate(dl, env);
}

// unary operators

NodePtr UnaryOperatorNode::create(const std::string& name, NodePtr&& arg)
{
  std::unique_ptr<UnaryOperatorNode> res;
  if (name == "!")
    res = std::make_unique<NotUnaryOperatorNode>();
  else
    throw std::runtime_error("invalid unary operator " + name);

  res->arg = std::move(arg);
  return res;
}

ValueNodePtr NotUnaryOperatorNode::evaluate(const deal &dl, const Environment &env) const
{
  return IntValueNode::create(arg->evaluate(dl, env) ? 1 : 0);
}

// binary operators

NodePtr BinaryOperatorNode::create(const std::string& name, NodePtr&& lhs, NodePtr&& rhs)
{
  std::unique_ptr<BinaryOperatorNode> res;
  if (name == "&&" || name == "and")
    res = std::make_unique<AndBinaryOperatorNode>();
  else
    throw std::runtime_error("invalid binary operator " + name);

  res->lhs = std::move(lhs);
  res->rhs = std::move(rhs);
  return res;
}

ValueNodePtr AndBinaryOperatorNode::evaluate(const deal &dl, const Environment &env) const
{
  auto l = lhs->evaluate(dl, env);
  auto r = rhs->evaluate(dl, env);
  return IntValueNode::create(l && r);
}

#define PARSE_OPERANDS(type1, type2)                                           \
  auto l_node = lhs->evaluate(dl, env);                                        \
  if (l_node->as_##type1() == nullptr)                                         \
    throw std::runtime_error("invalid type for lhs: expected " #type1);        \
  auto r_node = rhs->evaluate(dl, env);                                        \
  if (r_node->as_##type2() == nullptr)                                         \
    throw std::runtime_error("invalid type for rhs: expected " #type2);        \
  auto l = *(l_node->as_##type1());                                            \
  auto r = *(r_node->as_##type2());


ValueNodePtr GreaterThanBinaryOperatorNode::evaluate(const deal &dl, const Environment &env) const
{
  PARSE_OPERANDS(int, int);
  return IntValueNode::create(l > r);
}

// functions

NodePtr FunctionNode::create(const std::string& name, std::vector<NodePtr>&& args)
{
  std::unique_ptr<FunctionNode> res;
  if (name == "hcp")
    res = std::make_unique<HCPFunctionNode>();
  else
    throw std::runtime_error("invalid function " + name);

  res->args = std::move(args);
  return res;
}

#define xstr(a) str(a)
#define str(a) #a
#define PARSE_ARG(name, idx, type)                                             \
  auto name##_node = args[idx]->evaluate(dl, env);                             \
  if (name##_node->as_##type() == nullptr)                                     \
    throw std::runtime_error(                                                  \
        "invalid type for argument " #idx                                      \
        " in function " xstr(__func__) ": expected " #type);                   \
  auto name = *(name##_node->as_##type());

ValueNodePtr HCPFunctionNode::evaluate(const deal &dl, const Environment &env) const
{
  int hcp = 0;
  if (args.size() == 1) {
    PARSE_ARG(seat, 0, int);
    for (int i = 0; i < 4; ++i)
      hcp += calc_hcp(dl.remainCards[seat][i]);
  }
  else if (args.size() == 2) {
    PARSE_ARG(seat, 0, int);
    PARSE_ARG(suit, 1, int);
    hcp = calc_hcp(dl.remainCards[seat][suit]);
  }
  else {
    throw std::runtime_error("expected 1 or 2 arguments");
  }

  return IntValueNode::create(hcp);
}

// values

// base conversions -- return null
const std::string *ValueNode::as_string() const { return nullptr; }
const int *ValueNode::as_int() const { return nullptr; }
const std::vector<int> *ValueNode::as_int_vector() const { return nullptr; }

// string
ValueNodePtr StringValueNode::create(const std::string& s)
{
  auto res = std::make_unique<StringValueNode>();
  res->value = s;
  return res;
}
ValueNodePtr StringValueNode::evaluate(const deal &dl, const Environment &env) const
{
  return StringValueNode::create(value);
}
StringValueNode::operator bool() const { return !value.empty(); }
const std::string *StringValueNode::as_string() const { return &value; }


// int
ValueNodePtr IntValueNode::create(int i) {
  auto res = std::make_unique<IntValueNode>();
  res->value = i;
  return res;
}
ValueNodePtr IntValueNode::evaluate(const deal &dl, const Environment &env) const {
  return IntValueNode::create(value);
}
IntValueNode::operator bool() const { return value != 0; }
const int *IntValueNode::as_int() const { return &value; }

// int vector
ValueNodePtr IntVectorValueNode::create(std::initializer_list<int> v)
{
  return IntVectorValueNode::create(v.begin(), v.end());
}
ValueNodePtr IntVectorValueNode::evaluate(const deal &dl, const Environment &env) const {
  return IntVectorValueNode::create(value.begin(), value.end());
}
IntVectorValueNode::operator bool() const { return !value.empty(); }
const std::vector<int> *IntVectorValueNode::as_int_vector() const { return &value; }
