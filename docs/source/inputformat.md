# Dealer Scripts

This documentation is nothing more than a translation in to markdown of the [original documentation](https://www.bridgebase.com/tools/dealer/Manual/input.html), included here for convenience. No attempt to update any of the information has been done, and other than formatting some bits as code blocks the layout has been preserved as much as possible.

## Basic Layout

The basic lay-out of the file is:
```
 command1 "parameters for command 1"
 command2 "parameters for command 2"
 ...
 condition "list of conditions"
 action "list of actions"
```
The exact format is free, as long as it is unambigous, the program will understand it; in other words, lines can be broken freely, wherever it is desired to do so. Any line starting with a `#`-sign is regarded as a comment and ignored.
Comments can also be placed at the **end** of any line, from a marker of `//` all the way to the end of the line; or, independent of line structure, by starting the comment with a marker of `/*` and ending it with a marker of `*/`.

## Lexical structure
All the words recognized by the program act as **keywords**, that is, **reserved** words -- you cannot use those words as identifiers for other purposes, or you will get a syntax error.
For many such keywords, both the singular and plural forms are recognized and accepted interchangeably; this also means both forms are reserved. This plural/singular duality applies to the following keywords: **club**, **diamond**, **heart**, **spade**, **notrump**, **hcp**, **jack**, **queen**, **king**, **ace**, **loser**, **control**, **trick** and **imp**.

## Inputs
The program knows several basic commands, each consisting of a keyword and a parameter. A parameter can be a single value or an expression that will be evaluated for every generated deal. Besides that, the program allows the user to create identifiers and assign expressions to them. The identifiers can be used as parameters for the basic commands or inside other expressions, and this is exactly equivalent to using the expressions they denote.

* **generate (number)**
  generate (number) hands. If you do not specify this, then a million hands will be generated

* **produce (number)**
  Produce (number) hands that satisfy the condition. If you do specify this and you want the hands to be printed you get 40. If you only asked for statistics or so you will get a 100,000.
  The "generate" and "produce" numbers are upper limits. The first one to become true will terminate the program.

* **vulnerable ({none|NS|EW|all})**
  Sets the vulnerability for the hand to 1 of the 4 possibilities, with none the default if the command is not in the input file.
  This command is primarily intended for cases where `action-list` includes the `printpbn` action and the hands will be fed into another program for further analysis. These programs often require that the dealer and vulnerability are known. This command allows the user to set the vulnerability, the next command allows him to set the dealer.

* **dealer (compass)**
  Sets the dealer on the hand to north, south, east or west, with north the default if the command is not in the input file.

* The predeallist consists of a player, followed by holding in one or more suits separated by commas. A holding in a suit consist of a suit-symbol (S, H, D or C) followed by cards (AKQJ, T for 10, 9..2).

  A player can be pre-dealt any number of cards, e.g. for a play problem it is possible to give dummy and declarer their specific hands and the opening-leader the card he just led. The program then generates hands by dividing the remaining 25 cards over the two other players.

  An alternate form of predeal specification is `(suit)(player)==1` (for example: `spades(north)==1` and variants thereof for different suits, compass positions, numbers); this will ensure that (player) gets exactly the number of spades specified, (in this case, one), but that spade can be any card (except for the ones predealt to other players). `predeal (player),(card)` will just force the program to give these cards to this player, without any restrictions for the remaining cards. For example, predeal north,S2 will give north the 2 of spades. However, all other spade cards can still be dealt to north, so north will not necessarily have a singleton spade 2.

  Note that `predeal` is not compatible with a command-line switch of "-l", and only makes much sense for hands that are not permuted if the command-line switches of "-2" or "-3" are given ("-3" is generally used with predeal for North, "-2" with predeal for North and South) to specify "swapping" (the default is "-0", "no swapping").

* **pointcount (list of numbers)**
  Points to give to the various cards, starting from the ace and ending with the 2. The `hcp()` function uses this. Default is the standard 4, 3, 2, 1 (and 0 for all other cards) scale.

* **altcount (number) (list of numbers)**
  Similar to pointcount, but for 10 "alternate counts" numbered 0 to 9, so that several things about a hand can be "counted". The ptN() functions use this (names are pt0, pt1, etc, up to pt9, and there are also synonyms such as tens, jacks, etc; default for what is being counted varies for each of the 10 alternate counts).

* **condition (expression)**
  For every generated hand, the expression is evaluated. If it is true (non zero), then the corresponding action is executed. If you do not specify a condition the constant 1 (always true) will be assumed.
  The word condition can actually be omitted. Note that if more than one condition is specified, this is not diagnosed as an error, but the last condition will override the other(s); to have several conditions apply at once, you have to join them into a single expression, i.e. a single condition statement, joining them with "&&" or equivalently "and".

  Deals not meeting the condition are considered to be "generated" but not "produced", and no action is undertaken for them.

* **action (actionlist)**
  List of actions to be executed. If you do not specify an action, the printall action is assumed. If more than one action is in the list, separate them with commas.
  
* **(identifier) = (expression)**
  Defines (identifier) to represent (expression)
  
## Expressions
  An expression looks like regular C-code, with all normal operators that make sense in a bridge program present:

* `&&` or `and`: logical AND
* `||` or `or`: logical OR
* `!` or `not`: logical NOT
* `==`: Equal to (note, NOT "=", but rather "=="!!!)
* `!=`: Not equal to
* `<` and `<=`: Less and "Equal or Less" respectively.
* `>` and `>=`: Greater and "Greater or equal" respectively.
* `+`, `-`, `*`, `/`: Add, subtract, multiply and divide; note that division truncates to the next lower integer (the program does not use "floating point" numbers).
* `%`: Modulo ("remainder of division by").
* `()`: Brackets. The program uses the normal C-rules to evaluate expressions. With brackets this can be changed, e.g. 2*a+b is evaluated by multiplying a by 2, then adding b. Changing this into 2*(a+b) reverses this.
* `?:` the ternary "selection" operator. The operand before the ? is first evaluated; if true, then the one right after the ? and before the : is evaluated (and its value is that of this entire sub-expression), else, the one at the end of the sub-expression, i.e. after the :. This operator is usually used for "if-then-else" constructions.

For example: Suppose you want assign the number of hcp in north's longest minor to a variable. With the selection operator, this can be done as follows:
```
minornorth = clubs(north) > diamonds(north) ? hcp(north,clubs) : hcp(north,diamonds)
```
The program will first evaluate the `clubs(north)>diamonds(north)` part. If this is true, then `hcp(north,clubs)` will be assigned to `minornorth`. If not, then `minornorth` will be set to `hcp(north,diamonds)`. This line is equivalent to the following piece of C-like code:
```c
if (clubs(north) > diamonds(north) )
  minornorth = hcp(north, clubs);
else
  minornorth = hcp(north, diamonds);
```
Besides that, special operators useful in a bridge-program are provided:
* Suit Lengths
  * **(suit) ( (compass) )**, eg `hearts(west)`
the number of cards in the suit held by the player. Suit can be `club(s)`, `diamond(s)`, `heart(s)` or `spade(s)`.
* Hand Evaluation
  * **hcp ( (compass) )**, eg `hcp(north)`
the number of high card points held by the player using the 4321 count, unless overwritten with the pointcount command.
  * **hcp ( (compass), (suit) )**, eg `hcp(south, spades)`
the number of high card points in the specified suit, using the 4321 count (or alternate assignments provided with the pointcount command).
  * **ptN ( (compass) )**, eg `pt3(north)`
alternate-count number N (from 0 to 9) for the player named
  * **ptN ( (compass), (suit) )**, eg `ptN(south, spades)`
the value of alternate-count number N using the specified suit and player
  * **tens, jacks, queens, kings, aces, top2, top3, top4, top5, c13**
alternate, readable synonyms for pt0 to pt9 in order -- the names correspond to what these alternate-counts do count if not overridden with the altcount command: number of jacks/queens/kings/aces; numbers of honours in the top 2 (AK), 3 (AKQ), 4 (AKQJ), 5 (AKQJT); "c13" points, with A=6, K=4, Q=2, J=1 (a version of the "Four Aces" or "Burnstine" count using only integers, and with points in each suit that sum to 13, whence the name). Example: top5(east,spades) number of honours that East holds in the Spade suit (unless alternate count number 8 has been overridden with altcount 8, in which case the things being counted can be quite different).
  * **control ((compass))**, eg `control(north)`
The number of controls using A=2, K=1. It is possible to generate hands with N controls using the hcp() function. However, one has to override the standard pointcount table for that, making it impossible to generate hands with requirements on hcp and controls (for example, " hcp(north)>6 and control(north)<3"). This function solves that problem.
  * **control ((compass, (suit))**, eg `control(north, spades)`
The number of controls using A=2, K=1 in a suit.
  * loser ((compass)), eg `loser(north)`
The number of losers in the hand, or the sum of the number of losers in each suit. The program does not apply any corrections to the loser-count such as "1 loser less if a player has more aces than queens".
  * **loser ((compass, (suit))**, eg `loser(north, spades)`
The number of losers in a suit. The number of losers in a suit is:
3 cards or more: 3 - 1 for each of A, K or Q held.
Void: 0 losers.
Singleton A: 0 losers, any other singleton 1.
Doubleton AK: 0 losers, Ax or Kx 1, any other doubleton 2.
  * **cccc(compass)**
  * **quality(compass, suit)**
Both quality and cccc use the algorithms described in _The Bridge World_, October 1982, with the single exception that the values are multiplied by 100 (so that we can use integers for them). Thus, a minimum opening bid is about 1200, rather than 12.00 as expressed in the text.
  * **tricks(compass, strain)**
Runs GIB's double-dummy engine (BRIDGE under Linux, BRIDGE.EXE under Windows/NT or /98), which must be present on the path or in the same directory as the Dealer executable (together with, on Windows, SH.EXE and CYGWIN.DLL from Cygnus' free Cygwin package; this latter is not necessary in Paul Baxter's version), to compute the number of tricks that, at double-dummy par, will be taken by the given declarer in the given strain (suit or notrumps).
  * **score(vulnerability, contract, tricks)**
Returns the positive or negative score that declarer will make if the given contract, at the given vulnerability condition, is played and the given number of tricks are made. The syntax for "contract" is of the form "x3N" for 3 no-trumps, "x7C" for 7 clubs, etc; the leading "x" is needed. There is currently no way to specify that the contract is doubled, nor that it is re-doubled. The result will be positive if the contract makes, negative if it goes down.
  * **imps(scoredifference)**
Translates a score-difference into IMPs (International Match Points). The difference, of course, can be positive or negative, and the result of "imps" will then have that same sign.
* Shapes and specific cards
  * **shape ( (compass), shapelist)**
  This function specifies specific shapes for a player.
  The shapelist is a list of shapes combined with + or - signs. A shape with a + sign is added to the list, a shape with a - sign is excluded from the list.
  
    A shape is specified by digits in the normal order spades, hearts, diamonds and clubs, so 5431 specifies a hand with 5 spades, 4 hearts, 3 diamonds and a singleton club.
  
    Digits can be replaced by the letter "x" to match any length, so "55xx" specifies a hand with 5 spades, 5 hearts and 3 cards in the minors.
  
    The `any` operator can be prepended to a shape. This will remove the order of the suits, so `any 4333` specifies any hand with 1 4-card suit and 3 cards in the 3 other suits.
  
    Adding all this together allows you to write expressions like:
  
    ```
    shape(north, any 4333 + 54xx - any 0xxx)
    ```
  
    requiring north to hold any 4333, 5 spades and 4 hearts, but excluding any distribution with a void.
    This operator is one of the most important in the program and is very efficiently implemented. Any shape() call, no matter how complicated is executed in constant time. Use `shape()` for all length expressions if you can.

  * **hascard ( (compass), (card) )**, eg `hascard(east, TC)`
whether east holds the 10 (T) of clubs

## Actions
Note that multiple `print` actions, while not forbidden, are not guaranteed to work sensibly. `printoneline` and `printes` are roughly "designed" to work with each other, but most other combinations will not produced the overall hoped-for output format; experiment. Actions whose names do not start with "print", i.e. `average` and `frequency`, do generally co-operate sensibly with each other and with one print action (or a series of `printoneline`/`printes` ones), but, again, experiment is advised.
The different actions are:

* **printall**
prints all four hands next to each other in the order north, east, south and west. This is the default.
* **print ((list of compasses))**, eg `print(east,west)`
print all hands specified on separate pages. This is the best way to generate hands to be used for partnership training. One of the partners gets one page, and one the other and they can start practicing.
* **printew**
Prints the east and west hands only, with west to the left of east. This is useful for generating examples for bidding sequences. Generate the 2 hands then add comments in a text editor to the file.
* **printpbn**
Print the output in PBN format, for further analysis by other programs.
* **printcompact [optional expression]**
Print the output, and optionally an expression, in reasonably compact form (4 lines per deal).
* **printoneline [optional expression]**
Print the output, and optionally an expression, in very compact form (1 line per deal).
* **printes (list of strings and expressions)**
  Prints one or more expressions and strings; separate them with commas if there is more than one, and use \n to indicate end of line. Example: `printes "Number of hearts: ", hearts(north), \n`
  This is mainly intended to help you debug complicated expressions -- break them up into small pieces and use printes to examine their results.
* **average "optional string" (expr)**, eg `average "points" hcp(north)`
calculates and prints the average of the expression over all hands satisfying the condition. The optional strings is printed before the average.
* **frequency "optional string" ( (expr), (lowbnd), (highbnd) )**
calculates and prints a histogram of the values of (expr), between the bounds (lowbnd) and (highbnd) inclusive (all values lower than lowbnd are cumulated into a first row "Low", all higher than highbnd into a last row "High"). The optional string is printed before the histogram
* **frequency "optional string" ( (expr), (lowbnd), (highbnd), (expr2), (lowbnd2), (highbnd2) )**
calculates and prints a 2-D histogram of the joint values of (expr), between the bounds (lowbnd) and (highbnd) inclusive, and (expr2) between the bounds (lowbnd2) and (highbnd2) inclusive; as above, "low" and "high" are added for each expression, and, also, the marginals of the joint distribution are printed as "Sum" rows and columns. This can give a good idea of the mutual statistical influence of two computed expressions upon each other. The optional string is printed before the histogram.
The program allows for and unlimited number of actions. More than one print action is allowed, but, depending on the actions involved, this may or may not give the desired results.
## An example
Back to the "you hold ..." problem. Suppose we want to generate 25 hands that match these specifications on a slow machine, so we don't want to generate too many hands. This is accomplished with the following input file:
```
generate   10000
produce    25
vulnerable EW
dealer     west
predeal    south SAQ542, HKJ87, D32, CAK
west1c   = hcp(west)>11 && clubs(west)>= 3
# Condition describing west's 1C opener.
north2d  = diamonds(north)>=6 && (hcp(north)>5 && hcp(north)<12)
# Condition describing north's 2D overcall.
condition  west1c && north2d
# Require that west bids 1C and north 2D
action     printall
```
This produces 25 hands, including, for example, with this one:
```
J 7 3               9 8                 A Q 5 4 2           K T 6
3                   9 6 4 2             K J 8 7             A Q T 5
K Q J T 9 8 5       7                   3 2                 A 6 4
T 5                 9 8 7 4 3 2         A K                 Q J 6
```
Note that the hands that you get depend on the seed of the random generator, so, unless you use the `-s` flag to set the random generator seed, the hands that you produce will be different.
You can now start to analyze the hand and decide on the best action for east. However, if you look carefully at the west-hand, then you see that west could have opened this with a 15-17 NT. If you look at other hands, west might have opened 1D, 1H or 1S. These hands are excluded by:
```
west1d = diamonds(west)>clubs(west) || ((diamonds(west)==clubs(west))==4)
west1h = hearts(west)>= 5
west1s = spades(west)>= 5
west1n = shape(west, any 4333 + any 4432 + any 5332 - 5xxx - x5xx) &&
         (hcp(west)>14 && hcp(west)<18)
west1c = hcp(west)>11 && clubs(west)>= 3 &&
         (not west1n) && (not west1s) && (not west1h) && (not west1d)
```
A next run shows that north will occasionally overcall 2D on 8-card suit or with a side 4 or 5 card major. These distributions are excluded with:
```
north2d = (hcp(north)>5 && (hcp(north)<12) &&
          shape (north, xx6x + xx7x - any 4xxx - any 5xxx)
```
making the complete example:
```
generate   10000
produce    25
vulnerable ew
dealer     west
predeal    south SAQ542, HKJ87, D32, CAK
west1n = shape(west, any 4333 + any 4432 + any 5332 - 5xxx - x5xx) &&
         hcp(west)>14 && hcp(west)<18
west1h = hearts(west)>= 5
west1s = spades(west)>= 5
west1d = diamonds(west)>clubs(west) || ((diamonds(west)==clubs(west))==4)
west1c = (not west1n) && hcp(west)>10 && clubs(west)>=3
         && (not west1h) && (not west1s) && (not west1d)
north2d = (hcp(north)>5 && hcp(north)<12) &&
          shape(north, xx6x + xx7x - any 4xxx - any 5xxx)
condition  west1c && north2d
action     printall
```
A number of examples can be found in [Examples.zip](https://www.bridgebase.com/tools/dealer/Manual/Examples.zip).