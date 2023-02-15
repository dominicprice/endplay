#include <unordered_map>

#include "ast.h"

class Environment {
public:
  Environment();

  const NodePtr &get(const std::string &key) const;
  void set(const std::string &key, NodePtr &&value);
  void unset(const std::string &key);
  void reset();

private:
  std::unordered_map<std::string, NodePtr> data;
};
