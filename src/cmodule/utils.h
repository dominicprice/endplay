#include "types.h"

// deal and hand utilities
bool has_holding(Holding holding, Holding subholding);
int calc_hcp(Holding suit);
void clear_hand(Holding hand[4]);
void clear_deal(deal &dl);
Seat trick_winner(const deal &dl, Denom suit, Rank rank);
int cards_in_hand(Holding hand[4]);
void combine_hands(Holding hand1[4], const Holding hand2[4]);
int suit_length(Holding i);

// card utilities
int int_to_hcp(int r);

// dds function wrappers
void throw_on_fail(int err);

// print functions
void print_deal(const deal &dl, const std::string& title = " ");
void print_future_tricks(const futureTricks& fut, const std::string& title = " ");

// convert functions
deal pbn_to_deal(const std::string &pbn);
std::string deal_to_pbn(const deal &dl);
void pbn_to_hand(const std::string &pbn, Holding hand[4]);
std::string hand_to_pbn(const Holding hand[4]);
Rank char_to_rank(char c);
char rank_to_char(Rank r);
Denom char_to_denom(char c);
char denom_to_char(Denom d);
Holding rank_to_holding(Rank r);
Rank holding_to_rank(Holding holding);
std::string holding_to_pbn(Holding holding);
Seat char_to_seat(char c);
