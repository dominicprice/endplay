#include <iomanip>
#include <iostream>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "dealer.h"
#include "utils.h"

using namespace nlohmann;

Dealer::Dealer(const std::string& data)
{
  auto j = json::parse(data);
  RootNode* root;
  {
    NodePtr n = parse_json(j);
    root = dynamic_cast<RootNode*>(n.get());
    if (root == nullptr)
      throw std::runtime_error("tree must begin with a root node");
  }

  for (auto& child : root->children) {
    if (child->type() == Node::METADATA) {
      auto n = static_cast<MetadataNode*>(child.get());
      if (n->key() == MetadataNode::GENERATE)
        generate = n->generate();
      else if (n->key() == MetadataNode::PRODUCE)
        produce = n->produce();
      else if (n->key() == MetadataNode::VUL)
        vul = n->vul();
      else if (n->key() == MetadataNode::DEALER)
        dealer = n->dealer();
      else if (n->key() == MetadataNode::PREDEAL)
        predeal = n->predeal();
      else
        throw std::runtime_error("unknown metadata node key");
    }
    else if (child->type() == Node::ACTION) {
      auto n = static_cast<ActionNode*>(child.release());
      action.reset(n);
    }
    else if (child->type() == Node::DEFINITION) {
      auto n = static_cast<DefinitionNode*>(child.get());
      env.set(n->name, std::move(n->value));
    }
    else if (child->type() == Node::EXPRESSION) {
      auto n = static_cast<ExpressionNode*>(child.release());
      condition.reset(n);
    }
    else {
      throw std::runtime_error("unexpected node type");
    }
  }
}

NodePtr Dealer::parse_json(const json& j)
{
  int dtype = j["dtype"].get<int>();
  switch (dtype) {
  case 0: { // root
    std::vector<NodePtr> children;
    for (const auto& child : j["children"])
      children.push_back(parse_json(child));
    return RootNode::create(std::move(children));
  }
  case 1: { // symbol
    return SymbolNode::create(j["value"].get<std::string>());
  }
  case 2: { // operator
    auto name = j["value"].get<std::string>();
    const auto& children = j["children"];
    int nargs = children.size();
    if (nargs == 1) {
      auto arg = parse_json(j["children"][0]);
      return UnaryOperatorNode::create(name, std::move(arg));
    }
    else if (nargs == 2) {
      auto lhs = parse_json(j["children"][0]);
      auto rhs = parse_json(j["children"][1]);
      return BinaryOperatorNode::create(name, std::move(lhs), std::move(rhs));
    }
    else {
      throw std::runtime_error("operator node received more than 2 children");
    }
  }
  case 4: { // function
    auto name = j["value"].get<std::string>();
    std::vector<NodePtr> args;
    for (const auto child : j["children"])
      args.push_back(parse_json(child));
    return FunctionNode::create(name, std::move(args));
  }
  case 5: { // action
    // skip action nodes
  }
  case 6: { // value
    auto val = j["value"];
    if (val.is_string())
      return StringValueNode::create(val.get<std::string>());
    else if (val.is_number_integer())
      return IntValueNode::create(val.get<int>());
    else if (val.is_array())
      return IntVectorValueNode::create(val.begin(), val.end());
    else
        throw std::runtime_error("value node with invalid datatype");
  }
  default:
    throw std::runtime_error("node with invalid datatype " + std::to_string(dtype));
  }
}

// public definitions


void complete_partial_deal(deal &dl, const unsigned int remain_cards[4],
                           int handSize) {
  // Initial probability of each hand receiving a card
  int probs[4] = {handSize, handSize * 2, handSize * 3, handSize * 4};

  // std::cout << probs[0] << ' ' << probs[1] << ' ' << probs[2] << ' ' << probs[3] << '\n';

  // Adjust probabilities by the number of cards in each hand
  for (int hand = 0; hand < 4; ++hand) {
    for (int suit = 0; suit < 4; ++suit) {
      int count = suit_length(dl.remainCards[hand][suit]);
      for (int i = hand; i < 4; ++i)
        probs[i] -= count;
    }
  }

  // Adjust probabilities by removing a card if the hand has already played to
  // the trick
  for (int i = 0; i < 3; ++i) {
    int hand = (dl.first + i) % 4;
    if (dl.currentTrickRank[i] == 0)
      break;
    for (int j = hand; j < 4; ++j)
      --probs[j];
  }

  // Deal remaining cards
  for (unsigned int rank = 0; rank < 13; ++rank) {
    unsigned int rank_bit = 4u << rank;
    for (unsigned int suit = 0; suit < 4; ++suit) {
      // Return if there are no cards left to deal
      if (probs[3] == 0)
        return;
      // Skip if card already dealt or not in remain cards
      if (!(remain_cards[suit] & rank_bit))
        continue;
      // Pick a random number, and whichever range in probs
      // the number falls into we add the card to the corresponding
      // hand. We then decrement all elements in probs starting with
      // this hand. This reduces the probablility of a card being
      // dealt to the hand we just added a card too, and then adjusts
      // the other ranges to account for the fact that there is one
      // fewer card to deal.
      int k = rand() % probs[3];
      for (int i = 0; i < 4; ++i) {
        if (k < probs[i]) {
          dl.remainCards[i][suit] |= rank_bit;
          for (int j = i; j < 4; ++j)
            --probs[j];
          break;
        }
      }
    }
  }
}

void complete_full_deal(deal& dl)
{
	// Initialize probabilities and flatten dealt cards
	uint16_t predeal[4] = { 0, 0, 0, 0 };
	int probs[4] = { 13, 26, 39, 52 };
	for (int hand = 0; hand < 4; ++hand) {
		for (int suit = 0; suit < 4; ++suit) {
			int count = suit_length(dl.remainCards[hand][suit]);
			predeal[suit] |= dl.remainCards[hand][suit];
			for (int i = hand; i < 4; ++i)
				probs[i] -= count;
		}
	}

	// Deal remaining cards
	for (int rank = 0; rank < 13; ++rank) {
		uint16_t rank_bit = 4u << rank;
		for (int suit = 0; suit < 4; ++suit) {
			// Skip if card already dealt
			if (predeal[suit] & rank_bit)
				continue;
			// Pick a random number, and whichever range in probs
			// the number falls into we add the card to the corresponding
			// hand. We then decrement all elements in probs starting with
			// this hand. This reduces the probablility of a card being
			// dealt to the hand we just added a card too, and then adjusts
			// the other ranges to account for the fact that there is one
			// fewer card to deal.
			int k = rand() % probs[3];
			if (k < probs[0]) {
				dl.remainCards[0][suit] |= rank_bit;
				--probs[0], --probs[1], --probs[2], --probs[3];
			}
			else if (k < probs[1]) {
				dl.remainCards[1][suit] |= rank_bit;
				--probs[1], --probs[2], --probs[3];
			}
			else if (k < probs[2]) {
				dl.remainCards[2][suit] |= rank_bit;
				--probs[2], --probs[3];
			}
			else {
				dl.remainCards[3][suit] |= rank_bit;
				--probs[3];
			}
		}
	}
}
