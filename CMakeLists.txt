cmake_minimum_required(VERSION 3.13)
project(endplay)

#=================
# Global settings
#=================

if (NOT CMAKE_BUILD_TYPE)
  message(WARNING "CMAKE_BUILD_TYPE not specified; defaulting to 'Release'")
  set(CMAKE_BUILD_TYPE Release)
endif()
set(CMAKE_CXX_STANDARD 17)

set(ENDPLAY_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/endplay")
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" ENDPLAY_VERSION)
string(REGEX REPLACE "\n$" "" ENDPLAY_VERSION "${ENDPLAY_VERSION}")
string(TIMESTAMP ENDPLAY_BUILD_TIME)

# Detect compiler
if (CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
  set(CC_CLANG 1)
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  set(CC_GCC 1)
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
  set(CC_MSVC 1)
else()
  message(WARNING "The compiler you are using hasn't been tested for building this library.")
endif()

# Pretend to use SETUPTOOLS_BUILD variable to stop it complaining
if (SETUPTOOLS_BUILD)
  message(STATUS "Call to CMake was invocated by setuptools")
endif()

if (COMPILE_32_BITS)
  add_compile_options("-m32")
  add_link_options("-m32")
endif()

# Configure config.py with version number
configure_file("${ENDPLAY_ROOT_DIR}/config.py.in" "config.py" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/config.py" DESTINATION "endplay")


#=============
# dds library
#=============

# Source files
set(DDS_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/dds/")
set(DDS_SOURCE
  dds.cpp             dump.cpp            ABsearch.cpp
  ABstats.cpp         CalcTables.cpp      DealerPar.cpp
  File.cpp            Init.cpp            LaterTricks.cpp
  Memory.cpp          Moves.cpp           Par.cpp
  PlayAnalyser.cpp    PBN.cpp             QuickTricks.cpp
  Scheduler.cpp       SolveBoard.cpp      SolverIF.cpp
  System.cpp          ThreadMgr.cpp       Timer.cpp
  TimerGroup.cpp      TimerList.cpp       TimeStat.cpp
  TimeStatList.cpp    TransTableS.cpp     TransTableL.cpp)
if (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
  set(DDS_SOURCE ${DDS_SOURCE} exports.def dds.rc)
endif()
list(TRANSFORM DDS_SOURCE PREPEND "${DDS_ROOT_DIR}/src/")

# Target
add_library(dds OBJECT ${DDS_SOURCE})
target_compile_definitions(dds PRIVATE "DDS_THREADS_STL")
target_include_directories(dds PRIVATE "${DDS_ROOT_DIR}/src")

# Compiler specific flags
if (CC_GCC)
  target_compile_options(dds PRIVATE "-Wno-format-overflow")
elseif (CC_MSVC)
  target_compile_definitions(dds PRIVATE "_CRT_SECURE_NO_WARNINGS")
  target_compile_options(dds PRIVATE "/wd4267")
endif()

# Copy some macro definitions from the c header file into the
# __init__.py for the _dds package
file(READ "${DDS_ROOT_DIR}/include/dll.h" DDS_DLL_H)
string(REGEX MATCH "#define MAXNOOFBOARDS [0-9]+" DDS_MAXNOOFBOARDS "${DDS_DLL_H}")
string(REGEX MATCH "[0-9]+" DDS_MAXNOOFBOARDS "${DDS_MAXNOOFBOARDS}")
string(REGEX MATCH "#define MAXNOOFTABLES [0-9]+" DDS_MAXNOOFTABLES "${DDS_DLL_H}")
string(REGEX MATCH "[0-9]+" DDS_MAXNOOFTABLES "${DDS_MAXNOOFTABLES}")
configure_file("${ENDPLAY_ROOT_DIR}/_dds/__init__.py.in" "_dds/__init__.py" @ONLY)


#=========
# endplay c module
#=========

# Source files
set(CMODULE_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/cmodule/")
set(CMODULE_SOURCE
  action.cpp
  ast.cpp
  dealer.cpp
  env.cpp
  pyinterface.cpp
  utils.cpp)

list(TRANSFORM CMODULE_SOURCE PREPEND "${CMODULE_ROOT_DIR}")

# Target
add_library(endplay SHARED
  $<TARGET_OBJECTS:dds>
  ${CMODULE_SOURCE})
target_include_directories(endplay PRIVATE "${DDS_ROOT_DIR}/include")
target_link_libraries(endplay PUBLIC dds)

# Copy shared library name into the __init__.py file for the endplay package
set(ENDPLAY_LIBRARY_NAME "${CMAKE_SHARED_LIBRARY_PREFIX}endplay${CMAKE_SHARED_LIBRARY_SUFFIX}")
configure_file("${ENDPLAY_ROOT_DIR}/__init__.py.in" "__init__.py" @ONLY)


#================
# install target
#================

# Copy shared library into source tree
if (CC_MSVC)
  # .dll is a runtime component
  install(TARGETS dds RUNTIME DESTINATION "endplay/_dds")
else()
  install(TARGETS dds DESTINATION "endplay/_dds")
endif()

# Copy configured __init__.py files
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/_dds/__init__.py" DESTINATION "endplay/_dds/")
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/__init__.py" DESTINATION "endplay/")
