# Overview of submodules

*endplay* is divided into six main components, each of which can interoperate with each other:

- `endplay.types` is the basis for the whole library, providing the classes which are used by all the other modules for encapsulating the key objects in bridge. The 'master' class is `Deal`, whose state consists of the four hands in the deal, the cards played to the current trick,  a trump suit and the player to lead to the current trick. All the methods one would expect to  be defined on this are provided - accessing the hands, playing/unplaying cards from the current trick, importing and exporting from PBN format etc. From this class there is a hierarchy of types `Deal -> Hand -> SuitHolding -> Rank` which allows introspection of the deal at any level wanted. Many other types, such as containers for holding results from double dummy analysis and storing contracts, are also provided here.

- `endplay.dealer` provides functions for generating bridge hands. The main function is `generate_deals`  which can accept a list of constraints (either  functions which accept a `Deal` object and return `True`/`False`, or strings written in [dealer syntax](https://www.bridgebase.com/tools/dealer/Manual/input.html)) and generates a specified number of deals which satisfy the constraints. The `dealer` module can also be run as a main module with `python3 -m endplay.dealer` which works very similarly to the  Hans van Staveren [dealer program](https://www.bridgebase.com/tools/dealer/Manual/), but with some different output options and extra functionality.

- `endplay.evaluate` is the simplest component, consisting of a variety of functions which evaluate various properties of bridge hands, such as calculating high  card points, shape, losers, controls and other algorithms for estimating the quality of a hand.

- `endplay.dds` is a high-level wrapper around Bo Haglund's [dds library](https://github.com/dds-bridge/dds) which takes care of converting between the different types and encodings it uses internally and providing sensible defaults for things such as the number of threads it uses. A lower level wrapper `endplay._dds`, which is little more than the basic `ctypes` declarations, is also provided and is used internally by the dds functions when making library calls. 

- `endplay.parsers` provides tools for parsing common file types which are used as inputs and outputs for bridge software, this includes PBN and Dealer. These produce document tree representation of the input files and are used internally for many things, but can also be traversed manually to create programs which interact with other bridge software easily

- `endplay.interact` is a CLI tool which provides a simple REPL for analysing bridge deals. It can either be used via the `interact` function in the API, or as a main module with `python3 -m endplay.interact`

  

