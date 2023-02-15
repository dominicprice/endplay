#include "env.h"


Environment::Environment()
{
  reset();
}

const NodePtr &Environment::get(const std::string &key) const
{
  return data.at(key);
}

void Environment::set(const std::string &key, NodePtr &&value)
{
  data[key] = std::move(value);
}

void Environment::unset(const std::string &key)
{
  data.erase(key);
}

void Environment::reset()
{
  data.clear();
  data.emplace("pt0", IntVectorValueNode::create({0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt1", IntVectorValueNode::create({0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt2", IntVectorValueNode::create({0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt3", IntVectorValueNode::create({0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt4", IntVectorValueNode::create({1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt5", IntVectorValueNode::create({1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt6", IntVectorValueNode::create({1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt7", IntVectorValueNode::create({1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt8", IntVectorValueNode::create({1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0}));
  data.emplace("pt9", IntVectorValueNode::create({6, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0}));
}
