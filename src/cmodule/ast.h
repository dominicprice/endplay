#pragma once

#include <memory>
#include <string>
#include <variant>
#include <vector>

#include "dll.h"
#include "utils.h"

class Environment;

class Node;
class MetadataNode;
class DefinitionNode;
class ActionNode;
class ExpressionNode;
class ValueNode;

using NodePtr = std::unique_ptr<Node>;
using MetadataNodePtr = std::unique_ptr<MetadataNode>;
using DefinitionNodePtr = std::unique_ptr<DefinitionNode>;
using ActionNodePtr = std::unique_ptr<ActionNode>;
using ExpressionNodePtr = std::unique_ptr<ExpressionNode>;
using ValueNodePtr = std::unique_ptr<ValueNode>;

struct Node
{
  enum Type {
    ROOT,
    METADATA,
    ACTION,
    DEFINITION,
    EXPRESSION
  };

  virtual Type type() const = 0;
};

struct RootNode : Node
{
  static NodePtr create(std::vector<NodePtr> &&children);
  std::vector<NodePtr> children;

  virtual Type type() const override;
};

struct MetadataNode : Node
{
  enum Key {
    GENERATE,
    PRODUCE,
    VUL,
    DEALER,
    PREDEAL
  };

  template <typename ValueType>
  static MetadataNodePtr create(Key key, ValueType value);
  virtual Type type() const override;

  Key key() const;
  unsigned int generate() const;
  unsigned int produce() const;
  Vul vul() const;
  Seat dealer() const;
  deal predeal() const;

private:
  using ValueT = std::variant<unsigned int, Vul, Seat, deal>;
  Key key_;
  ValueT value_;
};

struct ActionNode : Node
{
  virtual Type type() const override;
  std::string key;
};

struct DefinitionNode : Node
{
  static DefinitionNodePtr create(const std::string& name, ExpressionNodePtr&& value);
  virtual Type type() const override;

  std::string name;
  ExpressionNodePtr value;
};

struct ExpressionNode : Node
{
  virtual Type type() const override;
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const = 0;
};

struct SymbolNode : ExpressionNode
{
  static NodePtr create(const std::string& name);
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
  std::string name;
};

struct UnaryOperatorNode : ExpressionNode {
  static NodePtr create(const std::string& name, NodePtr&& arg);

  NodePtr arg;
};

struct NotUnaryOperatorNode : UnaryOperatorNode {
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
};

struct BinaryOperatorNode : ExpressionNode {
  static NodePtr create(const std::string& name, NodePtr&& lhs, NodePtr&& rhs);

  NodePtr lhs;
  NodePtr rhs;
};

struct AndBinaryOperatorNode : BinaryOperatorNode {
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
};

struct GreaterThanBinaryOperatorNode : BinaryOperatorNode {
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
};

struct FunctionNode : ExpressionNode {
  static NodePtr create(const std::string& name, std::vector<NodePtr>&& args);

  std::vector<NodePtr> args;
};

struct HCPFunctionNode : FunctionNode {
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
};

struct ValueNode : ExpressionNode {
  virtual explicit operator bool() const = 0;
  virtual const std::string* as_string() const;
  virtual const int* as_int() const;
  virtual const std::vector<int>* as_int_vector() const;
};

struct StringValueNode : ValueNode {
  static ValueNodePtr create(const std::string& s);
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
  virtual explicit operator bool() const override;
  virtual const std::string *as_string() const override;

  std::string value;
};

struct IntValueNode : ValueNode {
  static ValueNodePtr create(int i);
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
  virtual explicit operator bool() const override;
  virtual const int *as_int() const override;

  int value;
};

struct IntVectorValueNode : ValueNode {
  template <typename It> static ValueNodePtr create(It begin, It end);
  static ValueNodePtr create(std::initializer_list<int> value);
  virtual ValueNodePtr evaluate(const deal &dl, const Environment &env) const override;
  virtual explicit  operator bool() const override;
  virtual const std::vector<int> *as_int_vector() const override;

  std::vector<int> value;
};

template <typename ValueType>
MetadataNodePtr MetadataNode::create(Key key, ValueType value) {
  auto res = std::make_unique<MetadataNode>();
  res->key_ = key;
  res->value_.emplace(value);
}

template <typename It>
ValueNodePtr IntVectorValueNode::create(It begin, It end)
{
  auto res = std::make_unique<IntVectorValueNode>();
  res->value.insert(res->value.begin(), begin, end);
  return res;
}
