#
# Generated Makefile for PyQt interfaces
#
# Created on Fri Aug 11 20:35:51 2017

PYUIC=pyuic5
SOURCES:=$(wildcard *.ui)
TARGETS=$(patsubst %.ui, ui_%.py, $(SOURCES))

all:	$(TARGETS)

ui_%.py: %.ui
	$(PYUIC) -o $@ $<

clean:
	rm -f ui_*.py *_rc.py *.pyc

distclean: clean

