# endplay

*endplay* is a Python library providing a variety of different tools for generating, analysing, solving and scoring bridge deals. It is a collection of different tools based on Bo Haglund's famous [dds library](https://github.com/dds-bridge/dds), Hans van Staveren's [dealer program](https://www.bridgebase.com/tools/dealer/Manual/) and other personal projects which have been cobbled together into a compatible interface using a common type system based on the encodings defined in the dds library.

## Status of this project

I began writing some of the components of this library many years ago, and it was only recently (as of the writing of this in late 2021) that I started to combine it together into one cohesive blob. One of the main results of this is that the quality of the code is extremely variable, the testing is wildly incomplete and there are still bits which are stubbed out and are currently item 296 on my to-do list.

With all that being said, I did think that the library was sufficiently complete, functional and useful that releasing it was worth the extra effort, but whether or not I will be actively maintaining it is an open question. If anyone finds the tools here useful, or has found them to be unuseful but wishes to try and fix them, then I would welcome any contributions no matter how small or total-rewritey they are. I have attempted to open bug reports for all the things which I wanted to get around to but haven't had time for yet, so if you are interested in contributing then do make yourself known by commenting on these, opening new bugs, sending me pull requests or by any other means (although joining my parish choir out of the blue might be a *tad* on the presumptuous side).

## Installation

*endplay* can be installed using pip with `python3 -m pip install endplay`.  In order to use the double dummy solving features in the `endplay.dds` module (and some of the other features which depend on this, such as generating hand records with double dummy results) you will need a copy of the compiled dds libary in your system's PATH. 

## Brief tour

*endplay* is divided into seven main components, each of which can interoperate with each other:

- `endplay.types` is the basis for the whole library, providing the classes which are used by all the other modules for encapsulating the key objects in bridge. The 'master' class is `Deal`, whose state consists of the four hands in the deal, the cards played to the current trick,  a trump suit and the player to lead to the current trick. All the methods one would expect to  be defined on this are provided - accessing the hands, playing/unplaying cards from the current trick, importing and exporting from PBN format etc. From this class there is a hierarchy of types `Deal -> Hand -> SuitHolding -> Rank` which allows introspection of the deal at any level wanted. Many other types, such as containers for holding results from double dummy analysis and storing contracts, are also provided here.
- `endplay.dealer` provides functions for generating bridge hands. The main function is `generate_deals`  which can accept a list of constraints (either  functions which accept a `Deal` object and return `True`/`False`, or strings written in [dealer syntax](https://www.bridgebase.com/tools/dealer/Manual/input.html)) and generates a specified number of deals which satisfy the constraints. The `dealer` module can also be run as a main module with `python3 -m endplay.dealer` which works very similarly to the  Hans van Staveren [dealer program](https://www.bridgebase.com/tools/dealer/Manual/), but with some different output options and extra functionality.
- `endplay.evaluate` is the simplest component, consisting of a variety of functions which evaluate various properties of bridge hands, such as calculating high  card points, shape, losers, controls and other algorithms for estimating the quality of a hand.
- `endplay.dds` is a high-level wrapper around Bo Haglund's [dds library](https://github.com/dds-bridge/dds) which takes care of converting between the different types and encodings it uses internally and providing sensible defaults for things such as the number of threads it uses. A lower level wrapper `endplay._dds`, which is little more than the basic `ctypes` declarations, is also provided and is used internally by the dds functions when making library calls. The dds library itself (`dds.so` or `dds.dll` on Windows) must be present on your machine's PATH for this module to function as this is loaded by `ctypes`.
- `endplay.scoring` provides an easy interface for calculating rankings based on a variety of common scoring metrics such as matchpoints, cross imps teams etc...
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
S T62
H Q
D AQT852
C QJT
>>> for h in d:
...   print(h)
974.AJ3.63.AK963
K83.K9752.7.8752
AQJ5.T864.KJ94.4
T62.Q.AQT852.QJT
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
>>> h.extend("SQ", "HA", "CT")
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
SQ, HA, CT
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
8                 ^S6       ---
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
  File "endplay\types\deal.py", line 115, in play
    raise RuntimeError("Trying to play card not in hand")
RuntimeError: Trying to play card not in hand
>>> d.play("HA", fromHand=False) # let's hope N isn't paying too much attention
```

Similarly `unplay` can be passed `toHand=False` to not move the picked-up card back into somebody's hand. The contents of the current trick can be examined by looking at the `curtrick` property which returns a list of cards played to the current trick, however this is a read-only object and modifying it will not alter the `Deal` object.

#### The `interact` module

One of my main motivations for building up this library is that sometimes I just want a quick way to see how a hand would play in a particular contract, or step through a deal card by card checking to see if a particular play would work. Using an interactive Python environment this is relatively easy, but in the end I developed a separate module called `interact` which implements (using the Python `cmd` library) its own REPL specifically for moving through a hand. It can be run by executing `python3 -m endplay.interact`. You will be greeted by a hand diagram of a randomly generated deal, and a prompt displaying the player currently on lead:

```
   Board 1    T6
    Vul -     AQ74
   N deals    AJT9
              A53
K843                        J5
J96                         KT853
KQ843                       762
6                           Q87
              AQ972
              2
              5
              KJT942
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
...   return hcp(deal.north) in [20, 22] and is_balanced(deal.north)
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

Running this on my machine takes a few minutes, even with only 30 hands, as the hand type is quite rare. In order to get some progress updates you can pass the `-m` flag which will display a progress bar as the hands are generated. To speed up generation of these sorts of hands, one of the swapping options can be passed which perform rotations on each shuffle: `-2` swaps the EW hands, and `-3` produces all permutations of the east, south and west hands. As the shuffle is a relatively expensive operation this can sometimes double the performance, however it does not interact well with the `predeal` command, as it will swap predealt hands.

### Evaluating deals





### Double dummy analysis



