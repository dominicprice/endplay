# Building and installing

## Using `pip`

*endplay* can be installed using pip with `python3 -m pip install endplay`. 

## From source

The compiled components of the library are build using CMake. `cd` into the root directory and then build with

```bash
mkdir out && cd out # Create the build directory
cmake -DCMAKE_BUILD_TYPE=Release .. # Configure and generate makefiles
cmake --build . # Compile the sources
cmake --build --target install . # Install the compiled files to the package tree
```

## Running the test suite

The test suite is implemented with the `unittest` library and can be run from the root directory with

```bash
python3 -m unittest
```



