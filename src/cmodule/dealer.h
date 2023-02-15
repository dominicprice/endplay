#pragma once

#include <string>
#include <vector>

#include "action.h"
#include "ast.h"
#include "dll.h"
#include "env.h"
#include "json.hpp"
#include "utils.h"

class Dealer {
public:
  Dealer(const std::string &data);
  std::vector<Action> run();

private:
  static NodePtr parse_json(const nlohmann::json& j);

  unsigned int generate;
  unsigned int produce;
  Vul vul;
  Seat dealer;
  deal predeal;

  ActionNodePtr action;
  ExpressionNodePtr condition;
  Environment env;
};

void complete_full_deal(deal& dl);
void complete_partial_deal(deal &dl, const unsigned int remain_cards[4], int hand_size);
