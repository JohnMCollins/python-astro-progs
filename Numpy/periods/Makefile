# Makefile for Fortran L-S routine
# NB relies on GNU make

build_host:=$(shell hostname)
PROGS=lsfort lsfort2
OBJECTS=lsfort.o lsfort2.o
CFILES=$(OBJECTS:.o=.c)

LDFLAGS=-s

G77=g77
G77FLAGS=-O2
G77LIBS=
F2C=f2c
F2CLIBS=-lf2c
MATHLIB=-lm

CC=cc
CFLAGS=-O2
RM=rm -f

all: $(PROGS)

ifneq (,$(findstring ac.uk, $(build_host)))
lsfort: lsfort.o
	$(G77) $(LDFLAGS) -o lsfort lsfort.o $(G77LIBS)

lsfort2: lsfort2.o
	$(G77) $(LDFLAGS) -o lsfort2 lsfort2.o $(G77LIBS)

%.o: %.f
	$(G77) $(G77FLAGS) -c $<
else
lsfort: lsfort.o
	$(CC) $(LDFLAGS) -o lsfort lsfort.o $(F2CLIBS) $(MATHLIB)

lsfort2: lsfort2.o
	$(CC) $(LDFLAGS) -o lsfort2 lsfort2.o $(F2CLIBS) $(MATHLIB)

%.o: %.f
	$(F2C) $<
	$(CC) $(CFLAGS) -c $*.c
	$(RM) $*.c
endif

clean:
	$(RM) $(PROGS) $(OBJECTS)
ifeq (,$(findstring ac.uk, $(build_host)))
	$(RM) $(CFILES)
endif
