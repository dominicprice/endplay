#pragma once

#include <vector>
#include <string>
#include "dll.h"

// holdings
typedef unsigned int Holding;
#define H2 0x0004
#define H3 0x0008
#define H4 0x0010
#define H5 0x0020
#define H6 0x0040
#define H7 0x0080
#define H8 0x0100
#define H9 0x0200
#define HT 0x0400
#define HJ 0x0800
#define HQ 0x1000
#define HK 0x2000
#define HA 0x4000

#define FOR_EACH_HOLDING(h) for (Holding h = HA; h >= H2; h >>= 1)

// ranks
typedef unsigned int Rank;
#define R2 2
#define R3 3
#define R4 4
#define R5 5
#define R6 6
#define R7 7
#define R8 8
#define R9 9
#define RT 10
#define RJ 11
#define RQ 12
#define RK 13
#define RA 14

#define FOR_EACH_RANK(r) for (Rank r = RA; r >= R2; --r)

// denoms
typedef unsigned int Denom;
#define SPADES   0
#define HEARTS   1
#define DIAMONDS 2
#define CLUBS    3
#define NOTRUMPS 4

// seats
typedef unsigned int Seat;
#define NORTH 0
#define EAST  1
#define SOUTH 2
#define WEST  3

// vulnerability
typedef unsigned int Vul;
#define NONE 0
#define BOTH 1
#define NS   2
#define EW   3

