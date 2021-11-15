# endplay

*endplay* is a Python library providing a variety of different tools for generating, analysing, solving and scoring bridge deals. It is a collection of different tools based on Bo Haglund's famous [dds library](https://github.com/dds-bridge/dds), Hans van Staveren's [dealer program](https://www.bridgebase.com/tools/dealer/Manual/) and other personal projects which have been cobbled together into a compatible interface using a common type system based on the encodings defined in the dds library.

If you find this useful and would like to contribute, or found it totally buggy and broken and want to fix it, then I am very open to contributions.

## Building and installing

### Using `pip`

*endplay* can be installed on some systems from PyPI using pip with `python3 -m pip install endplay`. 

If it isn't built for your operating system, or version of Python (both at the moment very likely, as I have only built binaries for the two operating systems I use), then you can also ask pip to build it from this repo by running `python3 -m pip install git+https://github.com/dominicprice/endplay.git`. Note that this will require you to have a C++ compiler on your system.

### From source

*endplay* uses `setuptools` to manage its build and can be built with the `build` package:

```bash
# Clone repo and submodules
git clone --recursive https://github.com/dominicprice/endplay.git
cd endplay
# Only build is required to start the build, other packages 
# are automatically fetched
python3 -m pip install build
# This will generate the wheel in the dist directory
python3 -m build
python3 -m pip install dist/endplay-<VERSIONSUFFIX>.whl
```

The compiled components of the library are built using CMake. An in-source build (for e.g. debugging) can be done by setting the install prefix to the current directory:

```bash
# Create the build directory
mkdir out && cd out
# Configure, generate makefiles and build
cmake -DCMAKE_BUILD_TYPE=<Debug|Release> -DCMAKE_INSTALL_PREFIX=../endplay .. 
cmake --build . --target install --config <Debug|Release>
```

where one of the configurations `Debug` or `Release` should be specified. The `--config` parameter only needs to be passed with a toolset such as MSVC where the build type is not set at configuration time.

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
python3 -m unittest
```



## Overview of submodules

*endplay* is divided into six main components, each of which can interoperate with each other:

- `endplay.types` is the basis for the whole library, providing the classes which are used by all the other modules for encapsulating the key objects in bridge. The 'master' class is `Deal`, whose state consists of the four hands in the deal, the cards played to the current trick,  a trump suit and the player to lead to the current trick. All the methods one would expect to  be defined on this are provided - accessing the hands, playing/unplaying cards from the current trick, importing and exporting from PBN format etc. From this class there is a hierarchy of types `Deal -> Hand -> SuitHolding -> Rank` which allows introspection of the deal at any level wanted. Many other types, such as containers for holding results from double dummy analysis and storing contracts, are also provided here.

- `endplay.dealer` provides functions for generating bridge hands. The main function is `generate_deals`  which can accept a list of constraints (either  functions which accept a `Deal` object and return `True`/`False`, or strings written in [dealer syntax](https://www.bridgebase.com/tools/dealer/Manual/input.html)) and generates a specified number of deals which satisfy the constraints. The `dealer` module can also be run as a main module with `python3 -m endplay.dealer` which works very similarly to the  Hans van Staveren [dealer program](https://www.bridgebase.com/tools/dealer/Manual/), but with some different output options and extra functionality.

- `endplay.evaluate` is the simplest component, consisting of a variety of functions which evaluate various properties of bridge hands, such as calculating high  card points, shape, losers, controls and other algorithms for estimating the quality of a hand.

- `endplay.dds` is a high-level wrapper around Bo Haglund's [dds library](https://github.com/dds-bridge/dds) which takes care of converting between the different types and encodings it uses internally and providing sensible defaults for things such as the number of threads it uses. A lower level wrapper `endplay._dds`, which is little more than the basic `ctypes` declarations, is also provided and is used internally by the dds functions when making library calls. 

- `endplay.parsers` provides tools for parsing common file types which are used as inputs and outputs for bridge software, this includes PBN and Dealer. These produce document tree representation of the input files and are used internally for many things, but can also be traversed manually to create programs which interact with other bridge software easily

- `endplay.interact` is a CLI tool which provides a simple REPL for analysing bridge deals. It can either be used via the `interact` function in the API, or as a main module with `python3 -m endplay.interact`

  

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
>>> for h in d:
...   print(h)
974.AJ3.63.AK963
K83.K9752.7.8752
AQJ5.T864.KJ94.4
T62.Q.AQT852.QJT
```

If your terminal doesn't handle the Unicode suit symbols, then you can tell *endplay* to use the letters SHDC instead:

```python
>>> from endplay import config
>>> config.use_unicode = False
>>> w.pprint()
S T62
H Q
D AQT852
C QJT
```

The `Hand` object which is returned is bound to the data inside the deal, so any operations you perform on the hand will update the deal too; to get a copy of the hand which doesn't affect the deal object you should use the `copy` method. `Deal` also overloads the `__setitem__` function and accepts a `Hand` object which is copied into the deal, or a PBN string which sets the cards in the hand to the specified cards:

```python
>>> from endplay.types import Hand
>>> d = Deal()
>>> h = Hand("AQ..T964.QJ975")
>>> d.west = h
>>> d.west = "AQ..T964.QJ975" # equivalent
```

Modifying the contents of the hand can be done using the `add`, `extend` and `remove` methods. `add` and `remove` return `True` if the the operation was successful: attempting to remove a card which isn't in a hand, or adding a card which is already there causes it to return `False`. 

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

The individual suit holdings in the hand can be examined by using the `spades`, `hearts`, `diamonds` and `clubs` properties or using the `__getitem__` operator. This returns a `SuitHolding` object which, like accessing hands of a deal, returns an object which is bound to the data in the hand. Many of the methods defined in `Hand` are also defined in `SuitHolding`, but use the `Rank` class instead of the `Card` class:

```python
>>> s = h.spades
>>> s.add(Rank.R2)
True
>>> print(h)
Q2.A..T
>>> Rank.RQ in s
True
>>> for card in s:
...   print(card)
Rank.RQ
Rank.R2
```

Holdings in a hand can be specified using the `__setitem__` operator too:

```python
>>> h.diamonds = "9752"
```

Moving back to the `Deal` object itself, as well as the four hands it also contains some other information such as the trump suit, player on lead and cards played to the current trick. Many functions in the *endplay* library will ignore these values, but the double dummy solving algorithms in particular may rely on these to provide accurate results. The trump suit and player on lead can be set by setting the `tump` and `first` properties respectively:

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

Similarly `unplay` can be passed `toHand=False` to not move the picked-up card back into somebody's hand. The contents of the current trick can be examined by looking at the `curtrick` property which returns a list of cards played to the current trick, however this is a read-only object and attempting to modify it will not alter the `Deal` object.

#### Enumerated types

*endplay* exposes five enumerated types: `Denom`, `Penalty`, `Player`, `Rank` and `Vul`. These all have a fairly consistent interface to make handling them as convenient as possible:

- They have a static `find` method which allows them to be constructed from a string, e.g. `Denom.find("hearts")`, `Penalty.find("x")` or `Vul.find("ew")`. There are often multiple ways of expressing these objects as strings (suit-symbols vs letters, *luv* vs *none* for vulnerability etc.) and the `find` method does its best to convert whatever string you give it into a value. This raises a `ValueError` if the conversion fails
- As well as the `name` property inherited from `Enum` which returns a lowercase string, they also have an `abbr` property which return a one or two character abbreviation for the object. This is used by e.g. the `Card` class to construct a string representation of the card (the `__str__` method consists of the single line `return f"{self.suit.abbr}{self.rank.abbr}"`)

All enumerations can have their members iterated over using e.g. `for x in Player` , however many also provide functions which allow iterating over the elements in a different order or over a subset of the elements (e.g. `Denom.suits()`, `Denom.bidorder()`). A full list of the methods can be found in the API reference of the documentation.

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
2. There are 16 cards in the play history, but only 13 cards in the output. Two things are going on here: a) the number of tricks before any card is played is appended to the front and b) as the last four cards are all forced and noone can alter the outcome of the contract at this stage these are not calculated by the algorithm. Therefore the number of cards returned in this instance is 16 (cards in play history) + 1 (starting tricks) - 4 (remove final trick) = 13.

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
  W  0  2  4  0  0
  E  0  2  4  0  0
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
  W  0  0  0  0  0
  E  0  0  0  0  0
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

