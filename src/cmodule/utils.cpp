#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string.h>
#include <strings.h>

#include "utils.h"

// internal data structures
unsigned short int dbitMapRank[16] = {
    0x0000, 0x0000, 0x0001, 0x0002, 0x0004, 0x0008, 0x0010, 0x0020,
    0x0040, 0x0080, 0x0100, 0x0200, 0x0400, 0x0800, 0x1000, 0x2000};

unsigned char dcardRank[16] = {'x', 'x', '2', '3', '4', '5', '6', '7',
                               '8', '9', 'T', 'J', 'Q', 'K', 'A', '-'};

unsigned char dcardSuit[5] = {'S', 'H', 'D', 'C', 'N'};
unsigned char dcardHand[4] = {'N', 'E', 'S', 'W'};


// internal functions

void equals_to_string(int equals, char *res) {
  int p = 0;
  int m = equals >> 2;
  for (int i = 15; i >= 2; i--) {
    if (m & static_cast<int>(dbitMapRank[i]))
      res[p++] = static_cast<char>(dcardRank[i]);
  }
  res[p] = 0;
}


// public functions

bool has_holding(Holding holding, Holding subholding)
{
  return holding & subholding;
}

int calc_hcp(unsigned int suit)
{
  return 4 * has_holding(suit, HA) + 3 * has_holding(suit, HK) +
         2 * has_holding(suit, HQ) + 1 * has_holding(suit, HJ);
}

void clear_deal(deal &dl)
{
  memset(dl.remainCards, 0, sizeof(dl.remainCards[0][0]) * 4 * 4);
  memset(dl.currentTrickRank, 0, sizeof(dl.currentTrickRank) * 3);
  memset(dl.currentTrickSuit, 0, sizeof(dl.currentTrickSuit) * 3);
  dl.first = 0;
  dl.trump = 0;
}

void clear_hand(unsigned int hand[])
{
  memset(hand, 0, sizeof(int) * 4);
}

Seat trick_winner(const deal& dl, Denom suit, Rank rank)
{
  int winner = dl.first;
  int top_rank = dl.currentTrickRank[0];
  int top_suit = dl.currentTrickSuit[0];

  if (dl.currentTrickSuit[1] == top_suit) {
    if (dl.currentTrickRank[1] > top_rank) {
      top_rank = dl.currentTrickRank[1];
      top_suit = dl.currentTrickSuit[1];
      winner = (dl.first + 1) % 4;
    }
  }
  else if (dl.currentTrickSuit[1] == dl.trump) {
    top_rank = dl.currentTrickRank[1];
    top_suit = dl.currentTrickSuit[1];
    winner = (dl.first + 1 % 4);
  }

  // std::cout << dl.currentTrickSuit[2] << " " << top_suit << '\n';
  if (dl.currentTrickSuit[2] == top_suit) {
    if (dl.currentTrickRank[2] > top_rank) {
      top_rank = dl.currentTrickRank[2];
      top_suit = dl.currentTrickSuit[2];
      winner = (dl.first + 2) % 4;
    }
  }
  else if (dl.currentTrickSuit[2] == dl.trump) {
    top_rank = dl.currentTrickRank[2];
    top_suit = dl.currentTrickSuit[2];
    winner = (dl.first + 2 % 4);
  }

  if (suit == top_suit) {
    if (rank > top_rank) {
      winner = (dl.first + 3) % 4;
    }
  }
  else if (suit == dl.trump) {
    winner = (dl.first + 3) % 4;
  }

  return Seat(winner);
}

int cards_in_hand(unsigned int hand[4])
{
  int n = 0;
  for (int i = 0; i < 4; ++i) {
    int k = suit_length(hand[i]);
    n += k;
  }
  return n;
}

void combine_hands(unsigned int hand1[4], const unsigned int hand2[4])
{
  for (int i = 0; i < 4; ++i)
    hand1[i] |= hand2[i];
}

int suit_length(unsigned int i)
{
  int n = 0;
  FOR_EACH_RANK(rank) {
    if (i & rank) ++n;
  }
  return n;
}


// card utilities

int rank_to_hcp(Rank r)
{
  switch (r) {
  case RA: return 4;
  case RK: return 3;
  case RQ: return 2;
  case RJ: return 1;
  default: return 0;
  }
}

// dds function wrappers

void throw_on_fail(int err) {
  if (err != RETURN_NO_FAULT) {
    char errString[80];
    ErrorMessage(err, errString);
    throw std::runtime_error(errString);
  }
}


// print functions


void print_deal(const deal &dl, const std::string &title)
{
  constexpr size_t full_line = 80;
  constexpr size_t hand_offset = 12;
  constexpr size_t hand_lines = 12;

  int c, h, s, r;
  char text[hand_lines][full_line];

  for (int l = 0; l < hand_lines; l++)
  {
    memset(text[l], ' ', full_line);
    text[l][full_line - 1] = '\0';
  }

  for (h = 0; h < DDS_HANDS; h++)
  {
    int offset, line;
    if (h == 0)
    {
      offset = hand_offset;
      line = 0;
    }
    else if (h == 1)
    {
      offset = 2 * hand_offset;
      line = 4;
    }
    else if (h == 2)
    {
      offset = hand_offset;
      line = 8;
    }
    else {
      offset = 0;
      line = 4;
    }

    for (s = 0; s < DDS_SUITS; s++)
    {
      c = offset;
      for (r = 14; r >= 2; r--)
      {
        if ((dl.remainCards[h][s] >> 2) & dbitMapRank[r])
          text[line + s][c++] = static_cast<char>(dcardRank[r]);
      }

      if (c == offset)
        text[line + s][c++] = '-';

      if (h != 3)
        text[line + s][c] = '\0';
    }
  }
  printf("%s", title.c_str());
  char dashes[80];
  int l = static_cast<int>(title.size()) - 1;
  for (int i = 0; i < l; i++)
    dashes[i] = '-';
  dashes[l] = '\0';
  printf("%s\n", dashes);
  for (int i = 0; i < hand_lines; i++)
    printf("%s\n", text[i]);
  printf("\n\n");
}

void print_future_tricks(const futureTricks &fut, const std::string &title) {
  printf("%s\n", title.c_str());

  printf("%6s %-6s %-6s %-6s %-6s\n", "card", "suit", "rank", "equals",
         "score");

  for (int i = 0; i < fut.cards; i++) {
    char res[15] = "";
    equals_to_string(fut.equals[i], res);
    printf("%6d %-6c %-6c %-6s %-6d\n", i, dcardSuit[fut.suit[i]],
           dcardRank[fut.rank[i]], res, fut.score[i]);
  }
  printf("\n");
}

// convert functions

deal pbn_to_deal(const std::string& pbn)
{
  deal dl;
  clear_deal(dl);
  dl.currentTrickRank[0] = 0;
  dl.first = 0;
  dl.trump = 0;
  int hand = 0;
  int i = 0;
  if (pbn[1] == ':') {
    hand = (int)char_to_seat(pbn[0]);
    i = 2;
  }
  int suit = 0;
  for (; i < pbn.length(); ++i) {
    if (pbn[i] == ' ') {
      hand = (hand + 1) % 4;
      suit = 0;
    }
    else if (pbn[i] == '.')
      ++suit;
    else {
      dl.remainCards[hand][suit] |= rank_to_holding(char_to_rank(pbn[i]));
    }
  }
  return dl;
}

void pbn_to_hand(const std::string& pbn, unsigned int hand[4])
{
  int suit = 0;
  for (char c : pbn) {
    if (c == '.')
      ++suit;
    else
      hand[suit] |= rank_to_holding(char_to_rank(c));
  }
}

std::string deal_to_pbn(const deal& dl)
{
  std::string ret = "N:";
  ret += hand_to_pbn(dl.remainCards[0]);
  ret.push_back(' ');
  ret += hand_to_pbn(dl.remainCards[1]);
  ret.push_back(' ');
  ret += hand_to_pbn(dl.remainCards[2]);
  ret.push_back(' ');
  return ret + hand_to_pbn(dl.remainCards[3]);
}


Rank char_to_rank(char c)
{
  switch (c) {
  case '2': return R2;
  case '3': return R3;
  case '4': return R4;
  case '5': return R5;
  case '6': return R6;
  case '7': return R7;
  case '8': return R8;
  case '9': return R9;
  case 't':
  case 'T': return RT;
  case 'j':
  case 'J': return RJ;
  case 'q':
  case 'Q': return RQ;
  case 'k':
  case 'K': return RK;
  case 'a':
  case 'A': return RA;
  default:
    throw std::runtime_error("could not convert char " + std::string(1, c) +
                             " to rank");
  }
}

char rank_to_char(Rank r)
{
  return dcardRank[(int)r];
}

Denom char_to_denom(char c)
{
  switch (c) {
  case 's':
  case 'S': return SPADES;
  case 'h':
  case 'H': return HEARTS;
  case 'd':
  case 'D': return DIAMONDS;
  case 'c':
  case 'C': return CLUBS;
  case 'n':
  case 'N': return NOTRUMPS;
  default: throw std::runtime_error("could not convert char " + std::string(1, c) + " to denom");
  }
}

char denom_to_char(Denom d)
{
  return dcardSuit[(int)d];
}

Holding rank_to_holding(Rank r)
{
  return 1u << (unsigned int)r;
}

Rank holding_to_rank(Holding holding)
{
  return Rank(__builtin_ffs(holding) - 1);
}

std::string holding_to_pbn(unsigned int holding)
{
  std::string res;
  for (unsigned int r = (unsigned int)HA; r >= (unsigned int)H2; r >>= 1) {
    if (holding & r)
      res += rank_to_char(holding_to_rank(r));
  }
  return res;
}

std::string hand_to_pbn(const unsigned int hand[4])
{
  std::string ret;
  for (int i = 0; i < 3; ++i) {
    ret += holding_to_pbn(hand[i]);
    ret.push_back('.');
  }
  return ret + holding_to_pbn(hand[3]);
}

Seat char_to_seat(char c)
{
  switch (c) {
  case 'n':
  case 'N': return NORTH;
  case 'e':
  case 'E': return EAST;
  case 's':
  case 'S': return SOUTH;
  case 'w':
  case 'W': return WEST;
  default: throw std::runtime_error("could not convert char" + std::string(1, c) + " to seat");
  }
}
