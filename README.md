# endplay

*endplay* is a Python library providing a variety of different tools for generating, analysing, solving and scoring bridge deals. It is a collection of different tools based on Bo Haglund's famous [dds library](https://github.com/dds-bridge/dds), Hans van Staveren's [dealer program](https://www.bridgebase.com/tools/dealer/Manual/) and other personal projects which have been cobbled together into a compatible interface using a common type system based on the encodings defined in the dds library.

If you find this useful and would like to contribute, or found it totally buggy and broken and want to fix it, then I am very open to contributions.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Building and installing](#building-and-installing)
  - [From PyPI](#from-pypi)
  - [From source](#from-source)
  - [Building the documentation](#building-the-documentation)
  - [Running the test suite](#running-the-test-suite)
- [Overview of submodules](#overview-of-submodules)
- [Tutorial](#tutorial)
  - [Inspecting deals](#inspecting-deals)
    - [Enumerated types](#enumerated-types)
    - [The `interact` module](#the-interact-module)
  - [Generating hands](#generating-hands)
    - [The main module](#the-main-module)
  - [Evaluating hands](#evaluating-hands)
  - [Double dummy analysis](#double-dummy-analysis)
    - [Analyse](#analyse)
    - [DD Tables](#dd-tables)
    - [Par contract calculation and scoring contracts](#par-contract-calculation-and-scoring-contracts)
    - [Bids and auctions: an aside](#bids-and-auctions-an-aside)
    - [Solving for a player's hand](#solving-for-a-players-hand)
  - [Parsing to and from bridge file formats](#parsing-to-and-from-bridge-file-formats)

## Building and installing

### From PyPI

Binary Python wheels are built and distributed on [PyPI](https://pypi.org/project/endplay/) for the following Python versions:

| Architecture | Windows  | Linux    | MacOS    |
| ------------ | -------- | -------- | :------- |
| x86          | 3.7-3.10 | N/A      | 3.7-3.10 |
| x64          | 3.7-3.10 | 3.7-3.10 | 3.7-3.10 |

On these systems `python3 -m pip install endplay` will install these pre-built wheels, otherwise it will attempt to install from the source distribution which requires a C++ compiler on your system. Note that *endplay* requires Python 3.7+.

The version of the library available on PyPI may be older than the current status of the repo, this is to ensure stability of these builds. For access to the latest bug fixes and preview features, you can install directly from the GitHub repo with `python3 -m pip install +git:https://github.com/dominicprice/endplay`

### From source

*endplay* uses `setuptools` to manage its build and can be installed with `pip`. 

```bash
# Clone repo and submodules
git clone --recursive https://github.com/dominicprice/endplay.git
cd endplay
python3 -m pip install .
```

If you are trying to develop for the library, then it is recommended to do all your testing in a virtual environment:

```bash
python3 -m pip install virtualenv
virtualenv venv
source venv/bin/activate # on windows, `cmd venv\scripts\activate`
python -m pip install . # installs into the created venv
```

You can then modify some files, and when you want to debug simply rerun `python -m pip install .` and the old build will be overwritten. This also has the advantage of being able to reuse the cache from the previous install (including the CMake cache) which speeds up build time.

If you want to build the binary wheels for you system, you can use the `build` package. This will create an isolated environment when collecting packages so you do not need to perform this in a virtual environment.

```bash
# Only build is required to start the build, other packages 
# are automatically fetched
python3 -m pip install build
python3 -m build # generates dist/endplay-<VERSIONSUFFIX>.whl
```

### Building the documentation

The documentation is semi-auto generated with sphinx. To build it, ensure that *endplay* is installed and then `cd` into the root directory and then run

```bash
cd docs
make html # or latex, or whatever output format you want
```

The documentation will be built in the `build` directory.

### Running the test suite

The test suite is implemented with the `unittest` library and can be run from the root directory with

```bash
python3 -m pytest
```



## Overview of submodules

*endplay* is divided into six main components, each of which can interoperate with each other:

- `endplay.types` is the basis for the whole library, providing the classes which are used by all the other modules for encapsulating the key objects in bridge. The 'master' class is `Deal`, whose state consists of the four hands in the deal, the cards played to the current trick,  a trump suit and the player to lead to the current trick. All the methods one would expect to  be defined on this are provided - accessing the hands, playing/unplaying cards from the current trick, importing and exporting from PBN format etc. From this class there is a hierarchy of types `Deal -> Hand -> SuitHolding -> Rank` which allows introspection of the deal at any level wanted. Many other types, such as containers for holding results from double dummy analysis and storing contracts, are also provided here.

- `endplay.dealer` provides functions for generating bridge hands. The main function is `generate_deals`  which can accept a list of constraints (either  functions which accept a `Deal` object and return `True`/`False`, or strings written in [dealer syntax](https://www.bridgebase.com/tools/dealer/Manual/input.html)) and generates a specified number of deals which satisfy the constraints. The `dealer` module can also be run as a main module with `python3 -m endplay.dealer` (or simply `endplay-dealer`) which works very similarly to the  Hans van Staveren [dealer program](https://www.bridgebase.com/tools/dealer/Manual/), but with some different output options and extra functionality.

- `endplay.evaluate` is the simplest component, consisting of a variety of functions which evaluate various properties of bridge hands, such as calculating high  card points, shape, losers, controls and other algorithms for estimating the quality of a hand.

- `endplay.dds` is a high-level wrapper around Bo Haglund's [dds library](https://github.com/dds-bridge/dds) which takes care of converting between the different types and encodings it uses internally and providing sensible defaults for things such as the number of threads it uses. A lower level wrapper `endplay._dds`, which is little more than the basic `ctypes` declarations, is also provided and is used internally by the dds functions when making library calls. 

- `endplay.parsers` provides tools for parsing common file types which are used as inputs and outputs for bridge software, this includes PBN and Dealer. These produce document tree representation of the input files and are used internally for many things, but can also be traversed manually to create programs which interact with other bridge software easily

- `endplay.interact` provides the `InteractiveDeal` class which keeps an undo stack whenever its state is modified, making it easier to interact with the deal. The main purpose of the module is a CLI tool which provides a simple REPL for analysing bridge deals which is available as a main module with `python3 -m endplay.interact` (or simply `endplay-interact`)

  

## Tutorial

### Inspecting deals

The `Deal` object is the class which is most frequently used in *endplay*. A deal can be constructed most simply by specifying it as a PBN string:

```python
>>> from endplay.types import Deal
>>> d = Deal("N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT")
```

The PBN string starts with a letter representing the first hand and a colon, and then each of the four hands separated by a space, where each hand consists of the cards in spades, hearts, diamonds and clubs respectively separated by a dot. The `__str__` method of the deal returns the deal as a PBN string, but a `pprint` method is provided to view the deal as a hand diagram:

```python
>>> print(d)
N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT
>>> d.pprint()
              974
              AJ3
              63
              AK963
T62                         K83
Q                           K9752
AQT852                      7
QJT                         8752
              AQJ5
              T864
              KJ94
              4
```

The four hands can be viewed by using the `north`, `east`, `south` and `west` properties, by using the `__getitem__` operator or by iterating over the deal to loop over all four hands:

```python
>>> d.north
Hand("974.AJ3.63.AK963")
>>> from endplay.types import Player
>>> w = d[Player.west]
>>> w.pprint()
♠ T62
♥ Q
♦ AQT852
♣ QJT
>>> for p, h in d:
...   print(h)
974.AJ3.63.AK963
K83.K9752.7.8752
AQJ5.T864.KJ94.4
T62.Q.AQT852.QJT
```

Note that iterating over the deal returns `(Player, Hand)` tuples. If your terminal doesn't handle the Unicode suit symbols, then you can tell *endplay* to use the letters SHDC instead:

```python
>>> from endplay import config
>>> config.use_unicode = False
>>> w.pprint()
S T62
H Q
D AQT852
C QJT
```

If there is a particular section of code which you would like to turn off unicode suit symbols for, for example if you are trying to export to export to a certain file format or would just like a particular piece of output to be formatted in plaintext, then you can use the `suppress_unicode` context manager:

```python
>>> config.use_unicode = True
>>> from endplay.config import suppress_unicode
>>> print(Denom.spades.abbr)
♠
>>> with suppress_unicode():
...   print(Denom.spades.abbr)
S
>>> print(Denom.spades.abbr)
♠
```

The `Hand` object which is returned is bound to the data inside the deal, so any operations you perform on the hand will update the deal too; to get a copy of the hand which doesn't affect the deal object you should use the `copy` method. `Deal` also overloads the `__setitem__` function and accepts a `Hand` object which is copied into the deal, or a PBN string which sets the cards in the hand to the specified cards:

```python
>>> from endplay.types import Hand
>>> d = Deal()
>>> h = Hand("AQ..T964.QJ975")
>>> d.west = h
>>> d.west = "AQ..T964.QJ975" # equivalent
```

Modifying the contents of the hand can be done using the `add`, `extend` and `remove` methods. `add` and `remove` return `True` if the operation was successful: attempting to remove a card which isn't in a hand, or adding a card which is already there causes it to return `False`. 

```python
>>> h = Hand()
>>> h.add("SQ")
True
>>> print(h)
Q...
>>> h.extend(["SQ", "HA", "CT"])
2
>>> h.remove("D2")
False
```

`extend` returns the number of cards which were added to the hand. As well as specifying cards by strings, the `Card` class which stores a `Rank` and `Denom` object can also be used:

```python
>>> from endplay.types import Card, Rank, Denom
>>> c = Card(suit=Denom.hearts, rank=Rank.R9)
>>> c in h # or "H9" in h
False
>>> len(h)
3
>>> print(", ".join(str(c) for c in h))
♠Q, ♥A, ♣T
```

`Card` objects are immutable, but should not be tested for equality using identity (i.e. use `==` not `is`). The individual suit holdings in the hand can be examined by using the `spades`, `hearts`, `diamonds` and `clubs` properties or using the `__getitem__` operator. This returns a `SuitHolding` object which, like accessing hands of a deal, returns an object which is bound to the data in the hand. Many of the methods defined in `Hand` are also defined in `SuitHolding`, but use the `Rank` class instead of the `Card` class:

```python
>>> s = h.spades
>>> s.add(Rank.R2)
True
>>> print(h)
Q2.A..T
>>> Rank.RQ in s
True
>>> for rank in s:
...   print(rank)
Rank.RQ
Rank.R2
```

Holdings in a hand can be specified using the `__setitem__` operator too:

```python
>>> h.diamonds = "9752"
```

Moving back to the `Deal` object itself, as well as the four hands it also contains some other information such as the trump suit, player on lead and cards played to the current trick. Many functions in the *endplay* library will ignore these values, but the double dummy solving algorithms in particular may rely on these to provide accurate results. The trump suit and player on lead can be set by setting the `trump` and `first` properties respectively:

```python
>>> d = Deal("65..2. .A.AK. .J.97. 8..83.")
>>> d.trump = Denom.hearts
>>> d.first = Player.south # not so fun, must concede all tricks to E
>>> d.first = Player.north # helicopter coup successful
```

Tricks can be played by using the `play` method, and picked up using the `unplay` method. By default, *endplay* attempts to take the card to be played from the hand who is currently on lead and will raise an error if they do not hold it.

```python
>>> d.play("S6") # north tries a coup-en-passant
>>> d.pprint()
              5
              ---
              2
              ---
8                 ^♠6       ---
---                         A
83                          AK
---                         ---
              ---
              J
              97
              ---
>>> d.play("DA") 
>>> d.unplay() # East picks back up the DA
>>> d.play("HA") # try ruffing instead...
>>> d.play("D9")
>>> d.play("S8")
>>> d.pprint()
              5
              ---
              2
              ---
---                         ---
---                         ---
83                          AK
---                         ---
              ---
              J
              7
              ---
>>> d.first
<Player.east: 1>
```

Notice how after the final card to the trick is played, the trick is cleared and `d.first` is assigned the winner of the trick. By passing `fromHand=False` to `play`, you can cause a card to be added to the current trick without attempting to remove it from anybody's hand:

```python
>>> d.play("HA") # can't play the HA again
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "endplay\types\deal.py", line 124, in play
    raise RuntimeError("Trying to play card not in hand")
RuntimeError: Trying to play card not in hand
>>> d.play("HA", fromHand=False) # let's hope N isn't paying too much attention
```

Similarly, `unplay` can be passed `toHand=False` to not move the picked-up card back into somebody's hand. The contents of the current trick can be examined by looking at the `curtrick` property which returns a list of cards played to the current trick, however this is a read-only object and attempting to modify it will not alter the `Deal` object.

#### Enumerated types

*endplay* exposes five enumerated types: `Denom`, `Penalty`, `Player`, `Rank` and `Vul`. These all have a fairly consistent interface to make handling them as convenient as possible:

- They have a static `find` method which allows them to be constructed from a string, e.g. `Denom.find("hearts")`, `Penalty.find("x")` or `Vul.find("ew")`. There are often multiple ways of expressing these objects as strings (suit-symbols vs letters, *luv* vs *none* for vulnerability etc.) and the `find` method does its best to convert whatever string you give it into a value. This raises a `ValueError` if the conversion fails
- As well as the `name` property inherited from `Enum` which returns a lowercase string, they also have an `abbr` property which return a one or two character abbreviation for the object. This is used by e.g. the `Card` class to construct a string representation of the card (the `__str__` method consists of the single line `return f"{self.suit.abbr}{self.rank.abbr}"`)

All enumerations can have their members iterated over using e.g. `for x in Player` , however many also provide functions which allow iterating over the elements in a different order or over a subset of the elements (e.g. `Denom.suits()`, `Denom.bidorder()`). A few other unique methods for the enumerated types include

- `Denom.is_major()`/`Denom.is_minor()`/`Denom.is_suit()`
- `Player.lho`/`Player.partner`/`Player.rho`. Rotating a player `n` positions left or right can be done with `Player.next(n)` and `Player.prev(n)`
- `Vul.from_board(n)` for determining vulnerability from board number. 
- `Rank` has a sister-class `AlternateRank` which is used internally by some double dummy routines, but should not be used outside of this context.

A full list of the methods can be found in the API reference of the documentation.

#### The `interact` module

One of my main motivations for building up this library is that sometimes I just want a quick way to see how a hand would play in a particular contract, or step through a deal card by card checking to see if a particular play would work. Using an interactive Python environment this is relatively easy, but in the end I developed a separate module called `interact` which implements (using the Python `cmd` library) its own REPL specifically for moving through a hand. It can be run by executing `python3 -m endplay.interact`. You will be greeted by an empty hand diagram. 

```
   Board 1    ---
    Vul -     ---
   N deals    ---
              ---
---                         ---
---                         ---
---                         ---
---                         ---
              ---
              ---
              ---
              ---
N>
```

You can specify a deal by typing `redeal <PBN string>`, or generate a random deal by typing `shuffle <constraint>` (more information on constraints can be found in the next section, *Generating hands*) 

```
N> shuffle hcp(north) > 20

   Board 1    KQT73
    Vul -     KQ
   N deals    K
              AKJ65
J64                         A852
J8                          T7654
QJ542                       A98
874                         9
              9
              A932
              T763
              QT32
N>
```

From here you can access many of the `Deal` and `Hand` methods; you can specify a deal by typing `redeal <PBN string>`, set a particular hand by typing `set <player> <PBN string>`, play a card by typing `play <card name>` and set the trump suit and player on lead with `trump <denom>` and `first <player>`. A full list of commands can be brought up by typing `help`, and more information on how a specific command works by typing `help <command name>`. This module also provides access to some of the double dummy solving features, the Python API of which is described farther down in this quick-start guide. 

### Generating hands

The `endplay.dealer` can be used to generate deals satisfying some constraints. The most basic usage is as follows:

```python
>>> from endplay.dealer import generate_deal
>>> generate_deal()
Deal('N:Q6.A872.KT3.J974 KT7.53.A42.AKQ85 AJ9853.KQ.J87.63 42.JT964.Q965.T2')
```

Constraints can be provided as functions which take a `Deal` object and return `True` or `False` based on some condition. The functions provided in the `endplay.evaluate` module are useful for specifying these. In the following example, we generate a list of 10 deals where north might open 2NT:

```python
>>> from endplay.evaluate import hcp, is_balanced
>>> def north_2nt(deal):
...   return 20 <= hcp(deal.north) <= 22 and is_balanced(deal.north)
...
>>> d = generate_deal(north_2nt)
>>> d.pprint()
              Q83
              AKQJ7
              A9
              KQ3
AK                          J7652
862                         T9
K75                         JT3
A8754                       962
              T94
              543
              Q8642
              JT
```

Instead of defining the named function `north_2nt`, we can of course also just provide an anonymous lambda to do the same thing. `generate_deal` can be passed an arbitrary number of constraints which must all be satisfied, so the above is equivalent to:

```python
>>> d = generate_deal(lambda deal: 20 <= hcp(deal.north) <= 22, lambda deal: is_balanced(deal.north))
```

Internally, `generate_deal` generates random deals and checks whether they satisfy the constraints until it finds one which does which it then returns. If many conditions are specified, or you wish to generate freak deals, then the number of deals which need to be generated might be very large. `generate_deal` will throw an exception if it generates enough deals that it doesn't think it will find a matching deal (defaulting to 1,000,000). This can be altered by providing the `max_attempts` parameter; if it is set to `-1` then it will never throw this exception.

`generate_deal` also accepts string constraints which contain expressions using the [dealer syntax](https://www.bridgebase.com/tools/dealer/Manual/input.html) which it will parse and evaluate on the deal, making the above condition for a north 2NT opening equivalent to the following:

```python
>>> d = generate_deal("hcp(north) >= 20 && hcp(north) <= 22 && shape(north, any 4333 + any 4432 + any 5332)")
```

This is ok for experimenting, but there is a large overhead involved with parsing and evaluating the string as this is currently all implemented in non-optimised Python, so if you are looking to do stats over many thousands of hands it is recommended to create a function instead. 

If you need to generate more than one deal then the generator function `generate_deals` is supplied. It accepts the exact same parameters as `generate_deal` with an extra `produce` parameter which defaults to 40. The deals are yielded, so if you want to collect them into a list then this must be done manually with `list(generate_deals())` , however iterating over the lists as they are generated can be done with the natural `for deal in generate_deals():` construct.

#### The main module

The `dealer` module can also be run as a program by executing `python3 -m endplay.dealer`. Without any arguments this will generate and print 40 random deals. The main usage of this script is to emulate the behaviour of the [dealer program](https://www.bridgebase.com/tools/dealer/Manual/) and so if it is passed a dealer script file then it will interpret and execute it, although the format of the output will not correspond 1:1 with original program. Dealer scripts allow simple as well as more advanced functions to be performed. A simple example of a dealer script is the following *stayman.dl* which produces hands where west opens a strong notrump and east has a Stayman hand and prints the two hands, which is useful for practicing partnership bidding.

```
produce 2 // Number of hands we want to output
west1n = 
	hcp(west) >= 15 && 
	hcp(west) <= 17 && 
	shape(west, any 4333 + any 4432 + any 5332)
eastStayman = 
	hcp(east) >= 10 &&
	(hearts(east) == 4 || spades(east) == 4) &&
	hearts(east) < 5 && spades(east) < 5
condition west1n && eastStayman
action printew
```

Running `python3 -m endplay.dealer -s 510 stayman.dl` outputs (with some whitespace trimmed)

```
AQ5                         KT76
Q54                         AKT8
AQ62                        JT
Q97                         T65


AJ                          96
J43                         AQ72
AJT7                        Q65
AT97                        K843
```

The `-s` parameter specifies a seed for the random number generator allowing reproducible results. Another use for the dealer module is to gather statistics about different hand types. The following script named *oops_2nt.dl* generates hands where north opens 2NT and finds south without any honours, and calculates the average number of tricks north can make double dummy playing the contract:

```
produce 30 // producing more will make the statistics more accurate
north2n =
    hcp(north) >= 20 &&
    hcp(north) <= 22 &&
    shape(north, any 4333 + any 4432 + any 5332)
disappointingSouth = hcp(south) == 0
condition north2n && disappointingSouth
action average tricks(north, notrumps)
```

Running this on my machine takes a few minutes, even with only 30 hands, as the hand type is quite rare. In order to get some progress updates you can pass the `-m` flag which will display a progress bar as the hands are generated. To speed up generation of these sorts of hands, one of the swapping options can be passed which perform rotations on each shuffle: `-2` swaps the EW hands, and `-3` produces all permutations of the east, south and west hands; by default the `-0` switch (no swapping) is used. As the shuffle is a relatively expensive operation this can improve performance, however it is not fully compatible with predealt hands. A (not particularly scientific) comparison of the three swapping algorithms is outlined here using the `stayman.dl` file using the seed `-s 1234` and the number of hands to produce increased to 1000:

| Swapping method          | Flag | `stayman.dl` runtime | Predeal compatibility |
| ------------------------ | ---- | -------------------- | --------------------- |
| No swapping              | `-0` | 53s                  | N✅ E✅ S✅ W✅           |
| 2-way swapping (E, W)    | `-2` | 46s (~13% faster)    | N✅ E❌ S✅ W❌           |
| 3-way swapping (E, S, W) | `-3` | 33s (~38% faster)    | N✅ E❌ S❌ W❌           |

Of course, had we set up `stayman.dl` to produce bidding patterns for north and south, 2-way swapping would be significantly worse as swapping the east west hands does not change the value of the predicate.

### Evaluating hands

When constructing constraints for use with the `generate_deal`/`generate_deals` functions, or performing statistics over deals, various metrics for evaluating the quality of various aspects of a hand are useful. *endplay* comes with a variety of functions for evaluating hands in the `endplay.evaluate` submodule. A full list of the functions contained in this submodule can be found in the API documentation; the list here is merely representative of the sorts of things which can be done.

#### Assigning point values to hands

By far the most well known and widely applied metric for calculating the quality of a hand is the traditional 'high card points' scale where we assign points to each of the face cards: 4 for an ace, 3 for a king, 2 for a queen and 1 for a jack. The `hcp` function can be used to evaluate a hand or suit holding using this metric:

```python
>>> from endplay.types import Hand
>>> from endplay.evaluate import hcp
>>> hand = Hand("AQ963.J64.852.K2")
>>> hcp(hand)
10
>>> hcp(hand.hearts)
1
```

Although the 4321 metric is the most widely applied, it is sometimes preferable to use a different scale. One such scale is the *Bergen scale* which assigns 4.5/3/1.5/0.75/0.25 to the top 5 cards. This scale is built into endplay as `bergen_hcp_scale` and the `hcp` can be told to use it by passing it as the second parameter:

```python
>>> from endplay.evaluate import bergen_hcp_scale
>>> hcp(hand, bergen_hcp_scale)
9.75
```

If you want to use your own custom scale, then you can pass a list of numbers containing the point values of the cards in the order A, K, Q, J, ..., 3, 2. If the list has less than 13 values, then it is assumed to be continued with zeroes:

```python
>>> custom_hcp_scale = [6,4,2,1] # A=6, K=4, Q=2, J=1, all other cards worth no points
>>> hcp(hand, custom_hcp_scale)
13
```

Another quality of the hand which is often described in terms of points is the distribution. A common system is to assign 3 points for a void, 2 points for a singleton and a single point for a doubleton. This is the standard behaviour of the `dist_points` function:

```python
>>> from endplay.evaluate import dist_points
>>> hand2 = Hand("AK.JT98765..Q963")
>>> dist_points(hand2)
4
>>> dist_points(hand2.diamonds)
3
```

As with the high card points scale, there are many different ways of counting points and so the `dist_points` function accepts a `scale` parameter which defines the counting method. *endplay* comes with five different scales built into the `evalute` module:

- `shortage_nofit_dist_scale`: The standard 3/2/1 scale
- `shortage_fit_dist_scale`: A 5/3/1 scale, often applied to a hand once a trump fit has been found
- `length_dist_scale`: Assigns a point for every extra card in a suit longer than 4, e.g. a five card suit is worth 1 point and a seven card suit is worth 3.
- `mixed_nofit_dist_scale`: A combination of `shortage_nofit_dist_scale` and `length_dist_scale`
- `mixed_fit_dist_scale`: A combination of `shortage_fit_dist_scale` and `length_dist_scale`

Custom scales can be passed as lists where the `n`th element (zero-indexed) is the number of points awarded to a suit of length `n`, and as with the `hcp` function the list is assumed to be padded with zeroes if later elements are omitted. As an example, the following scale just counts the number of tripletons in a hand:

```python
>>> tripletons = [0, 0, 0, 1]
>>> dist_points(hand, tripletons)
2
>>> dist_points(hand2, tripletons)
0
```

If a trump suit is found, then it usually the case that shortage points are not included in the calculation of distribution points. To account for this, `dist_points` also takes an `exclude` parameter with a list of suits to exclude from the calculation. Note that this is ignored if the object is a `SuitHolding` instead of a `Hand`:

```python
>>> dist_points(hand2, exclude=[Denom.spades])
3
>>> dist_points(hand2.diamonds, exclude=[Denom.diamonds])
3
```

High card points and distribution points are often combined into a scale known as 'total points'. In its most basic form, this is simply the sum of the two metrics:

```python
>>> from endplay.evaluate import total_points
>>> total_points(hand2) # = hcp(hand2) + dist_points(hand2) = 10 + 4
14
```

An optional `trump` parameter can be provided with a suit which is added to the `exclude` list of `dist_points`:

```python
>>> total_points(hand2, trump=Denom.spades)
13
```

Unprotected honours, i.e. honours which will drop if the opponents play higher honours from the top, are often discounted from the total points calculation. This can be enabled by setting the `protect_honours` flag:

```python
>>> total_points(hand) # 10 HCP and 1 doubleton
11
>>> total_points(hand, protect_honours=True) #Jxx drops and the point is removed
10
```

A more advanced method of calculating the overall strength of a hand is the [Kaplan Four Cs](http://www.rpbridge.net/8j19.htm) method which is implemented in the `cccc` algorithm:

```python
>>> from endplay.evaluate import cccc
>>> cccc(hand)
11.15
>>> cccc(hand2)
13.950000000000001
```

#### Evaluating shape

The shape of a hand can be evaluated using the `shape` and `exact_shape` functions; the former returns the shape ordered from longest to shortest whilst the latter always returns the shape in the order spades, hearts, diamonds and clubs:

```python
>>> from endplay.types import Hand
>>> from endplay.evaluate import shape, exact_shape
>>> h = Hand("AK92.A3.Q9.AK762")
>>> shape(h)
[5, 4, 2, 2]
>>> exact_shape(h)
[4, 2, 2, 5]
```

Various predicate functions are provided to query more generally the 'class' of the hand shape:

```python
>>> from endplay.evaluate import is_balanced, is_semibalanced, is_single_suited, is_two_suited
>>> is_balanced(h) # 4333, 4432 or 5332
False
>>> is_semibalanced(h) # balanced or 5422
True
>>> is_single_suited(h) # 6 or more cards in one suit
False
>>> is_two_suited(h) # 10 cards in two suits
False
```

There are more variants on these and optional parameters to fine tune their definitions, which can be found in the API documentation.




### Double dummy analysis

A particularly important feature of *endplay* is the ability to call routines from the [C++ dds library](https://github.com/dds-bridge/dds). The library is built and distributed with *endplay* so it is not necessary to have a copy of the library built on your machine. 

The double-dummy solving algorithms are split across four components:

- `endplay.dds.analyse` contains algorithms for analysing play sequences, calculating the maximum number of tricks which can be made after each card is played
- `endplay.dds.ddtable` has the functions for calculating double-dummy tables, showing the maximum number of tricks that each player could make in each contract
- `endplay.dds.par` provides par contract calculation algorithms
- `endplay.dds.solve` provides functions for calculating the maximum number of tricks each card in a player's hand can make

NB: out of laziness, I will often refer to 'maximum number of tricks' instead of 'double-dummy maximum number of tricks', i.e. the number of tricks that can be made assuming everybody at the table has perfect knowledge of where all the cards are and makes optimal plays at each opportunity. 

Most algorithms come in two variants, one which calculates a result for a single deal and a second which accepts multiple deals. The multiple deal variant is trivial to use if you understand how the single-deal versions work, so will not be covered here, but if you need to do calculations for multiple deals it is always better to use versions as they use multithreading and can reuse internal data structures.

#### Analyse

The `analyse` module consists of two pairs of functions: `analyse_play`/`analyse_all_plays` and `analyse_start`/`analyse_all_starts`.

The analysis functions are useful when you have the play history of a deal and want to see how optimal each card played was. Take [the following four card ending](https://www.bridgebum.com/coup_en_passant.php):

```python
>>> from endplay.types import Deal, Player
>>> d = Deal("AJ.6.A. KQ..K8. 4.A.Q4. 7..T.Q5", first=Player.south)
>>> d.pprint()
              AJ
              6
              A
              ---
7                           KQ
---                         ---
T                           K8
Q5                          ---
              4
              A
              Q4
              ---
```

The optimal play here is of course to unblock the ace of diamonds and then return to hand with a heart which squeezes east; the play history for this would be something like (depending on which losing option east goes for):

```python
>>> from endplay.dds import analyse_play
>>> history = [
...    "D4", "DT", "DA", "D8",
...    "H6", "DK", "HA", "S7",
...    "DQ", "C5", "SJ", "SQ",
...    "S4", "CQ", "SA", "SK"]
```

As everyone has played optimally (not that EW get much of a chance to make a mistake) running `analyse_play` will show that at each point in the play history EW can make no tricks:

```python
>>> h_analysis = analyse_play(d, history)
>>> print(", ".join(str(n) for n in h_analysis))
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
```

Despite being on the surface being nothing more than a computationally expensive way of printing a load of zeroes, it is worth noting two interesting things here:

1. The number of tricks is displayed from the perspective of the player to the right of player on lead. This is because it attempts to show declarers trick count, and in a full deal the declarer is to the right of the person on lead. In this case, as we have a four card ending with declarer on lead we can pass `declarer_is_first=True` to perform the swap and print `4, 4, 4, ...`
2. There are 16 cards in the play history, but only 13 cards in the output. Two things are going on here: a) the number of tricks before any card is played is appended to the front and b) as the last four cards are all forced and no-one can alter the outcome of the contract at this stage these are not calculated by the algorithm. Therefore the number of cards returned in this instance is 16 (cards in play history) + 1 (starting tricks) - 4 (remove final trick) = 13.

We all know that partner will never find this line though, so lets see what the function does when we play bridge ping-pong:

```python
>>> history2 = [
...    "HA", "C5", "H6", "SK",
...    "S4",  "S7", "SJ", "SQ"]
>>> h2_analysis = analyse_play(d, history2, declarer_is_first=True)
>>> print(", ".join(str(n) for n in h2_analysis))
4, 3, 3, 3, 4, 4, 4, 3, 3
```

We could find all the suboptimal plays by checking whether the number of tricks goes up or down after each card is played:

```python
>>> from itertools import pairwise # Python 3.10 upwards only
>>> for card, tricks in zip(history2, pairwise(h2_analysis)):
...     if tricks[0] != tricks[1]:
...         print(Card(card))
♥A
♠K
♠J
```

Cashing the ace at the start breaks up the squeeze, but when east incorrectly tosses a spade playing to the ace will drop the queen, however this leads to south finessing into east's now stiff queen.

Because the `analyse_play` function calculates the maximum tricks before any card is played, calling it with an empty play history is actually one of the most efficient ways of calculating the double dummy result of a deal. This is all `analyse_start` is - a wrapper for `analyse_play` with an empty play history.

#### DD Tables

The `ddtable` module consists of two functions, `calc_dd_table` and its multiple-deal variant `calc_all_tables`. The slight naming inconsistency is in order to keep the naming convention consistent with the original DDS library.

This is one of the simplest and most powerful functions in the `dds` module. Let's cast our minds back to 1975 with [this famous deal](http://www.rpbridge.net/7a31.htm) and remember just how thin the 7♣ contract really is: 

```python
>>> from endplay.types import Deal, Player, Denom
>>> from endplay.dds import calc_dd_table
>>> d = Deal("QJ8.AJ965.K82.AQ 43.QT87.QT64.754 AKT9..A97.J98632 7652.K432.J53.KT")
>>> table = calc_dd_table(d)
>>> table.pprint()
     ♣  ♦  ♥  ♠ NT
  N 13 10  9 13 13
  S 13 10  9 13 13
  E  0  2  4  0  0
  W  0  2  4  0  0
```

Individual results are accessible through the overloaded `__getitem__` operator:

```python
>>> assert(table[Denom.clubs, Player.south] == 13) # Filthy, but the assert passes
```

If, like me, you can never remember whether the table is indexed by strain or seat first, then luckily the operator is agnostic to which order you pass them:

```python
>>> assert(table[Player.south, Denom.clubs] == 13)
```

The multiple-deal variant `calc_all_tables` accepts an extra argument not available to `calc_dd_table` with a list of strains to be excluded from the calculation, if e.g. you want to calculate how a series of deals would play in notrumps and don't want to waste time calculating the table for the other strains. In this case, the results for all other strains will be set to 0. The `exclude` parameter can be any iterable, so `[Denom.notrumps, Denom.hearts]`would produce results for clubs, diamonds and spades, or in the example below we use `Denom.suits()` as a shorthand for excluding all the suits: 

```python
>>> from endplay.dds import calc_all_tables
>>> table, *_ = calc_all_tables([d], exclude=Denom.suits())
>>> table.pprint()
     ♣  ♦  ♥  ♠ NT
  N  0  0  0  0 13
  S  0  0  0  0 13
  E  0  0  0  0  0
  W  0  0  0  0  0
```

(NB: If you don't understand how `table, *_ =` works then don't worry, it is just a quick way to store the first element of the returned list into `table` and the other elements, in this case an empty list as we only requested one table, into the variable `_` which we will throw away.)

#### Par contract calculation and scoring contracts

The `endplay.dds.par` module contains only one function, `par`, which calculates the optimum contract on a deal, i.e. the lowest contract over which the opponents cannot bid any making contract and which sacrificing is too expensive. The par contracts are always returned as a list, as there are often multiple contracts which score the same (commonly the same contract played by either partner). As well as the deal (or double dummy table, as this is the only relevant information about the deal required) there are two more pieces of information which come into play:

1. The vulnerability, as this affects the score
2. The dealer, as there are occasions where i.e. both sides can make 1NT, and so the par contract depends on who gets to bid it first

Here are some examples of how the par function can be used:

```python
>>> from endplay.types import Deal, Vul, Player
>>> from endplay.dds import par
>>> d = Deal("N:AKQJ8..AT8632.43 T742.Q9543.J.QT8 63.AJT8.97.J7652 95.K762.KQ54.AK9")
>>> for contract in par(d, Vul.none, Player.north):
...     print(contract)
2♠N=
2♠S=
3♦N=
3♦S=
>>> for contract in par(d, Vul.ew, Player.north):
...     print(contract)
1♠N+1
1♠S+1
2♦N+1
2♦S+1
```

Notice that when EW become vulnerable, the level of the par contracts goes down as their possible sacrifice in hearts becomes too expensive. Note that if you have previously calculated the double dummy table for a board, then it is much more efficient to pass this instead of the `Deal` object:

```python
>>> from endplay.dds import calc_dd_table
>>> table = calc_dd_table(d)
>>> par(table, Vul.ew, Player.north) # saves `par` having to recalculate the DD table
```

The score associated with the par contracts is a property of the list-type object which holds the list of contracts, as it is of course constant across all the contracts. In the following high-stakes deal, NS can sacrifice in seven clubs over EW's heart slam:

```python
>>> d = Deal("N:J976..762.KQJ982 K5.JT9843.AK93.A AT42.765.J84.T54 Q83.AKQ2.QT5.763")
>>> parlist = par(d, Vul.ew, Player.north)
>>> parlist.score
-1100
```

The `Contract` class also has a `score` method which calculates the score of a contract based on a given vulnerability:

```python
>>> for contract in parlist:
...     print(contract.score(Vul.ew))
-1100
-1100
```

You can calculate the score of an arbitrary contract by constructing a `Contract` object and scoring it:

```python
>>> from endplay.types import Contract
>>> c = Contract("4HNx=") # construct from a string
>>> c.score(Vul.none)
590
>>> from endplay import Denom, Penalty
>>> c = Contract( # construct from values
... level = 4,
... denom = Denom.hearts,
... declarer = Player.north,
... penalty = Penalty.doubled,
... result = 0 # number of over/undertricks
)
>>> c.score(Vul.ns)
790
>>> c.result = -5
>>> c.score(Vul.ns)
-1400
```

#### Bids and auctions: an aside

While on the topic of contracts, it is worth mentioning the `Bid` class which represents a call in an auction. `Bid` objects are very weird, as they fulfill a double purpose of being able to represent *penalty actions*, i.e. "Pass", "Double" and "Redoule", as well as *contract actions* which name a strain and a level. These are represented by the `PenaltyBid` and `ContractBid` classes respectively, which derive from `Bid` but define different member variables - `PenaltyBid.penalty` vs `ContractBid.denom` and `ContractBid.level`. You can construct these directly using their `__init__` functions:

```python
from endplay.types import PenaltyBid, ContractBid, Penalty, Denom
>>> oneclub = ContractBid(2, Denom.hearts)
>>> double = PenaltyBid(Penalty.double)
```

or by using the `Bid` constructor to supply the name of the bid as a string:

```python
>>> twohearts = Bid("2H")
>>> double = Bid("double") # Bid("x") also works
```

Notice however that the type you get is actually always one of `PenaltyBid` or `ContractBid` - the `Bid` constructor will always automatically downcast the class instance to the appropriate type:

```python
>>> type(twohearts)
<class 'endplay.types.bid.ContractBid'>
>>> type(pass_)
<class 'endplay.types.bid.PenaltyBid'>
```

All bid class constructors also accept optional boolean `alertable` and string `announcement` parameters, of which none, either or both can be defined to allow for the case where e.g. thep oint range of a notrump bid is announced but not alertable:

```python
>>> unusual2nt = Bid("2H", announcement="Weak")
>>> forcing_pass = Bid("Pass", alertable=True, announcement="Forcing for one round")
```

The `alertable` and `announcement` attributes can be assigned and altered after construction of the `Bid` object, but the other properties are immutable. 

An auction is simply a list of bid objects:

```python
>>> auction = [ 
...   oneclub,     forcing_pass, two_hearts, double, 
...   Bid("Pass"), Bid("Pass"),  Bid("pass") ]
```

To calculate a contract from a given auction, you can use the `Contract.from_auction` method and provide the name of the first player to bid:

```python
>>> from endplay.types import Player, Contract
>>> Contract.from_auction(auction, Player.west)
Contract("2♥Ex=")
```

Any iterable of `Bid` objects satisfying the [`Reversible`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Reversible) interface can be passed as an auction.

#### Solving for a player's hand

The final module, `endplay.dds.solve`, provides the `solve_board`/`solve_all_boards` function pair which returns the number of tricks each card in a player's hand can yield. Let's go back to [a nice four card ending](https://www.bridgebum.com/criss_cross_squeeze.php):

```python
>>> d = Deal("Q2..6.A 5.632.. A..A.Q8 K4...K9", first=Player.south)
>>> d.pprint()
              Q2
              ---
              6
              A
K4                          5
---                         632
---                         ---
K9                          ---
              A
              ---
              A
              Q8
```

Can you work out how to pull off this squeeze? We can see what the optimal play is using `solve_board`:

```python
>>> from endplay import solve_board
>>> for card, tricks in solve_board(d):
...     print(card, tricks)
♦A 4
♠A 3
♣8 3
♣Q 3
```

We can then see west's options after south plays the ♦A by playing this to the trick:

```python
>>> d.play("DA")
>>> d.pprint()
              Q2
              ---
              6
              A
K4                          5
---                         632
---                         ---
K9                v♦A       ---
              A
              ---
              ---
              Q8
>>> for card, tricks in solve_board(d):
...     print(card, tricks)
♠4 0
♣9 0
♠K 0
♣K 0
```

Oops, out of luck! Notice how as opposed to the `analyse` family of functions, `solve_board` always returns the number of tricks the person playing the card can make.


### Parsing to and from bridge file formats

While not the primary aim of the library, *endplay* does support experimental parsing and writing of PBN and LIN file formats. These interfaces are in the `endplay.parsers` submodule, and aim to provide an interface consistent with that of the standard library parsing libraries. Each of the parsing packages `endplay.parsers.pbn` and `endplay.parsers.lin` provide four functions:
- `load`: Parse a file object into a list of `Board` objects
- `loads`: Parse a string into a list of `Board` objects
- `dump`: Write a list of `Board` objects to a file object
- `dumps` Write a list of `Board` objects to a string

Internally, each module provides `*Encoder` and `*Decoder` classes which do the heavy lifting. These can be used directly, but their interface may be unstable so cannot be recommended. 

The libraries store file information in lists of `endplay.types.Board` objects, which wrap a `Deal` as well as other information which is usually provided by these file formats. The full list of defined members can be found in the API reference as this is one of the bulkiest classes in *endplay*, in order to deal with the wealth of information that these file formats can store. We will present here a lighter introduction to the class by reading a PBN file and examining the result. We being by opening the sample PBN file in the examples directory and putting the first board into the variable `boardA`:

```python
>>> import endplay.parsers.pbn as pbn
>>> with open("examples/pbn_files/sample.pbn") as f:
...   boards = pbn.load(f)
>>> boardA = boards[0]
```

From here we can explore a lot of the basic information about the deal using the tools which we have already learned:

- The deal

```python
>>> boardA.deal.pprint()
              AT9
              2
              J432
              A9863
KJ85                        76432
AQT853                      4
9                           KQ
K4                          QJT72
              Q
              KJ976
              AT8765
              5
```

- The auction

```python
>>> from endplay.utils.io import pprint_auction
>>> pprint_auction(boardA.dealer, boardA.auction, include_announcements=True)
N    E    S    W    
P    P    1♥   P    
1NT  2♥*  3♦   4♠   
5♦   P    P    5♠*  
X    P    P    P    

2♥*: Spades & minor
5♠*: ♠
```

- The play history

```python
>>> from endplay.dds import analyse_play
>>> analyse_play(boardA.deal, boards[0].play)
<SolvedPlay object; data=(8, 9, 9, 9, 9, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8)>
```

- Meta-information about the board. As this can store just about anything you might want it can get a bit messy so don't worry if the code samples below go in one ear and out the other, for want of a better metaphor.

```python
>>> boardA.info.keys()
dict_keys(['Event', 'Site', 'Date', 'West', 'North', 'East', 'South', 'Dealer', 'Scoring', 'Score', 'Table', 'HomeTeam', 'VisitTeam', 'ScoreIMP', 'DoubleDummyTricks', 'OptimumResultTable', 'OptimumScore', 'Competition'])
>>> boardA.info.event # Dot access is case-insensitive
'TestingPBN'
>>> boardA.info["Site"] # Subscript access is case-sensitive
'SampleTestSite'
```

PBN tags ending in `Table` (but not equal to `Table` - that key is for the table number the board was played at) are tabular data, and entries in the `Board.info` dictionary which end in `Table` are treated differently; instead of having string values they are dictionaries with keys for the column headings and the rows:

```python
>>> from pprint import pprint
>>> pprint(boardA.info.OptimumResultTable)
{'headers': ['Declarer',
             {'alignment': 'R',
              'minwidth': '2',
              'name': 'Denomination',
              'ordering': None},
             {'alignment': 'R',
              'minwidth': '2',
              'name': 'Result',
              'ordering': None}],
 'rows': [['N', 'NT', '7'],
          ['N', 'S', '4'],
          ['N', 'H', '6'],
          ['N', 'D', '11'],
          ['N', 'C', '5'],
          ['W', 'NT', '5'],
          ['W', 'S', '8'],
          ['W', 'H', '6'],
          ['W', 'D', '2'],
          ['W', 'C', '7']]}
```
The `headers` key is a list of the column names; they can either be strings or dictionaries specifying how the columns should be displayed (see the API reference for more information). The `rows` key is a 2D list representing the rows of the table.

In sample.pbn, the second board contains some fields with value "#" indicating that they should be copied over from the previous board, these are automatically resolved:

```python
>>> boardB = boards[1]
>>> assert boardA.info.event == boardB.info.event
```

On the second board, the hand was passed out. The `Board` object is populated with an empty play history and a `Contract` object representing the pass:

```python
>>> boardB.play
[]
>>> boardB.contract
Contract("Pass")
```

Using the `endplay.parsers.lin` module, we can export these boards to LIN in order to use them on BBO:

```python
>>> import endplay.parsers.lin as lin
>>> l = lin.dumps(boards)
>>> print(l)
pn|JOHN SMITH,ARTHUR SOMEBODY,JORDAN PRESENTLY,EDWARD PEABODY|st||md|3S9TAH2D234JC3689A,S23467H4DQKC27TJQ,SQH679JKD5678TAC5,|rh||ah|Board 17|sv|o|mb|p|mb|p|mb|1H|mb|p|mb|1N|mb|2H|an| Spades & minor|mb|3D|mb|4S|mb|5D|mb|p|mb|p|mb|5S|an| !S|mb|d|mb|p|mb|p|mb|p|pg||pc|H2|pc|H4|pc|HK|pc|HA|pg||pc|D9|pc|D2|pc|DQ|pc|DA|pg||pc|C5|pc|C4|pc|CA|pc|C2|pg||pc|C9|pc|C7|pc|SQ|pc|CK|pg||pc|H6|pc|H8|pc|S9|pc|CT|pg||pc|C8|pc|CJ|pc|D5|pc|H3|pg||pc|S2|pc|D6|pc|SK|pc|SA|pg||pc|ST|pc|S3|pc|D7|pc|SJ|pg||mc|8|
pn|LOUISE FORWEES,JEAN JEANY,MARTINE ESPEREDO,BRENDA CALLOUGHWAY|st||md|1S29JAH478D6TJC3QA,S3467H3TQD23C69JK,S8TKH69AD59AC2457,|rh||ah|Board 11|sv|o|mb|p|mb|p|mb|p|mb|p|pg||
```

Suit symbols are automatically escaped using the `!S`, `!H` etc... names used by BBO. Of course, far less information is stored in a LIN file than a PBN file and so many of the fields in the `info` dictionary of the `Board` are lost during the conversion. We can of course also `load` a LIN file and `dump` it into a PBN file, any keys which the PBN file expects which aren't provided by the LIN file can either be specified by appending to the `Board.info` dictionary, or else they will be given the default value of `?` as specified by the [PBN standard](https://www.tistis.nl/pbn/).