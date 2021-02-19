#!/usr/bin/env python
from bwprotanalyzer import Protocol
import argparse

def main():
    PARSER = argparse.ArgumentParser("bwprotanalyzer", description="Analysiert eine BWPROT20.DAT-Datei, liest Änderungen und stellt (falls gewünscht) eine lesbare Log-Datei zur Verfügung")
    PARSER.add_argument("--output", required=False, help="BWPROT20 als Log-Datei in die angegebene Datei ausgeben (falls gewünscht)")
    PARSER.add_argument("input", help="Datei, welche eingelesen werden soll")
    
    args = PARSER.parse_args()
    proto = Protocol(args.input)
    
    if args.output:
        proto.to_log_file(args.output)
    else:
        proto.to_stdout()

if __name__ == '__main__':
    main()