import sys
from io import TextIOWrapper
import typing
import datetime
import enum

class ProtocolStatus(enum.IntEnum):
    NEW = 0
    CHANGE = 1
    DELETE = 2
    PRINT = 3
    DELETE_THROUGH_PROCESSING = 4

class ProtocolChange:

    def __init__(self, field: str, value: str, previous_value: str = "") -> None:
        self.field = field
        self.value = value
        self.previous_value = previous_value
    
    def __str__(self) -> str:
        return f"<Änderung {self.field}: {self.previous_value.strip()} -> {self.value.strip()}>"

class ProtocolEntry:

    def __init__(self, protocol_type: int, user: str, date: datetime.datetime, status: ProtocolStatus, index: str, changes: typing.List[ProtocolChange] = [], info: str = "", index_info: str = ""):
        self.protocol_type = protocol_type
        self.user = user
        self.date = date
        self.status = status
        self.index = index
        self.changes = changes
        self.info = info
        self.index_info = index_info
    
    def __str__(self) -> str:
        status_repr = ""
        if self.status == ProtocolStatus.NEW:
            if self.protocol_type == "000":
                status_repr = f"<Programmstart von Benutzer {self.user} am {self.date}>"
            elif self.protocol_type == "001":
                status_repr = f"<Programmende von Benutzer {self.user} am {self.date}>"
            else:
                status_repr = f"<Neuer Datensatz {self.index} in Bereich {self.protocol_type} von Benutzer {self.user} am {self.date}>"
        elif self.status == ProtocolStatus.CHANGE:
            status_repr = f"<Geänderter Datensatz {self.index} in Bereich {self.protocol_type} von Benutzer {self.user} am {self.date}>"
        elif self.status == ProtocolStatus.DELETE:
            status_repr = f"<Gelöschter Datensatz {self.index} in Bereich {self.protocol_type} von Benutzer {self.user} am {self.date}>"
        elif self.status == ProtocolStatus.PRINT:
            status_repr = f"<Gedruckter Datensatz {self.index} in Bereich {self.protocol_type} von Benutzer {self.user} am {self.date}>"
        elif self.status == ProtocolStatus.DELETE_THROUGH_PROCESSING:
            status_repr = f"<Gewandelter Datensatz {self.index} in Bereich {self.protocol_type} von Benutzer {self.user} am {self.date}>"
        else:
            status_repr = f"<Datensatz {self.index} in Bereich {self.protocol_type} von Benutzer {self.user} am {self.date}>"
        return status_repr

class Protocol:

    def __init__(self, file: str) -> None:
        self.file = file
        self.protocol = []

        self.__field_map__: typing.Dict[str, ProtocolChange] = {}
        self.__protocol_buffer__: typing.List[str] = []
    
    def load_protocol(self):
        with open(self.file, 'r', encoding='cp1252') as fp:
            protocol_block = []
            first_line = True
            for line in fp:
                if line.strip() == "": continue
                if line[:3] == "@PR":
                    if not first_line:
                        yield self.process_block(protocol_block)
                    else:
                        first_line = False
                    protocol_block = []
                protocol_block.append(line)
    
    def process_block(self, block: typing.List[str]):
        protocol_type, user, date, time, status, info = self.parse_pr_line(block[0])
        if len(block) < 2:
            return ProtocolEntry(protocol_type, user, datetime.datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M:%S"), ProtocolStatus(int(status)), "", info=info)
        true_index, index_info = self.parse_in_line(block[1])
        ae_block = block[2:]
        changes = [self.update_field(true_index, protocol_type, *self.parse_ae_line(line)) for line in ae_block]
        entry = ProtocolEntry(protocol_type, user, datetime.datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M:%S"), ProtocolStatus(int(status)), true_index, changes, info, index_info)
        return entry
    
    def parse_pr_line(self, line: str):
        # @PR,018,700,14.11.2020,21:00:00,1,PutRelation 00018
        split = line.split(",")
        protocol_type = split[1]
        user = split[2]
        date = split[3]
        time = split[4]
        status = split[5]
        info = split[6]
        return protocol_type, user, date, time, status, info

    def parse_in_line(self, line: str):
        # @IN,CON002                                                       Containererfassung - Pakete zuordnen                        
        split = line.split(",")
        index = split[1]
        true_index = index.split()[0]
        index_info = index[len(true_index):].strip()
        return true_index, index_info
    
    def parse_ae_line(self, line: str):
        # @AE,DBK86_0_6,CON002
        split = line.split(",")
        field = split[1]
        value = split[2]
        return field, value
    
    def update_field(self, index: str, dtype: str, field: str, value: str):
        map_idx = f"{index}_{dtype}_{field}"
        if map_idx in self.__field_map__:
            change = self.__field_map__[map_idx]
            new_change = ProtocolChange(field, value, change.value)
            self.__field_map__[map_idx] = new_change
        else:
            new_change = ProtocolChange(field, value, "unbekannt")
            self.__field_map__[map_idx] = new_change
        return new_change
    
    def to_log_file(self, path):
        with open(path, 'w', encoding='cp1252') as fp:
            for entry in self.load_protocol():
                line = None
                if entry.protocol_type == "000":
                    line = f"{entry.date}\t{entry.protocol_type}\tSTART\t{entry.user}\tBenutzer {entry.user} hat sich angemeldet"
                elif entry.protocol_type == "001":
                    line = f"{entry.date}\t{entry.protocol_type}\tEND\t{entry.user}\tBenutzer {entry.user} hat sich abgemeldet"
                elif entry.protocol_type == "020":
                    line = f"{entry.date}\t{entry.protocol_type}\tKASSESTART\t{entry.user}\tKasse {entry.user} hat sich angemeldet"
                elif entry.protocol_type == "021":
                    line = f"{entry.date}\t{entry.protocol_type}\tKASSEEND\t{entry.user}\tKasse {entry.user} hat sich abgemeldet"
                elif entry.protocol_type == "022":
                    line = f"{entry.date}\t{entry.protocol_type}\tKASSEDSTART\t{entry.user}\tKasse {entry.user} hat einen Tagesstart durchgeführt"
                elif entry.protocol_type == "023":
                    line = f"{entry.date}\t{entry.protocol_type}\tKASSEDEND\t{entry.user}\tKasse {entry.user} hat einen Tagesabschluss durchgeführt"
                elif entry.protocol_type == "031":
                    line = f"{entry.date}\t{entry.protocol_type}\tBELCORRECT\t{entry.user}\Bediener {entry.user} hat einen fehlerhaften Beleg automatisch korrigiert: {entry.index}"
                elif entry.protocol_type == "120":
                    line = f"{entry.date}\t{entry.protocol_type}\tNOTEDELETE\t{entry.user}\tBenutzer {entry.user} hat Notiztexte gelöscht"
                elif entry.protocol_type == "121":
                    line = f"{entry.date}\t{entry.protocol_type}\tGLOBALCANCEL\t{entry.user}\tBenutzer {entry.user} hat einen globalen Abbruch verursacht: {entry.info}"
                elif entry.protocol_type == "122":
                    line = f"{entry.date}\t{entry.protocol_type}\tREFERROR\t{entry.user}\tBenutzer {entry.user} hat einen Verweisfehler beim Laden einer Tabelle verursacht"
                elif entry.protocol_type == "123":
                    line = f"{entry.date}\t{entry.protocol_type}\tDIFFINDSATZ\t{entry.user}\tBenutzer {entry.user} hat eine Differenz zwischen Index und Satz festgestellt"
                elif entry.protocol_type == "126":
                    line = f"{entry.date}\t{entry.protocol_type}\tDUPLBELNR\t{entry.user}\tBenutzer {entry.user} hat versucht eine bestehende Belegnummer erneut anzulegen"
                elif entry.protocol_type == "128":
                    line = f"{entry.date}\t{entry.protocol_type}\tWAWILSTART\t{entry.user}\tBenutzer {entry.user} hat eine WAWI-Liste gestartet"
                elif entry.protocol_type == "130":
                    line = f"{entry.date}\t{entry.protocol_type}\tFIBULSTART\t{entry.user}\tBenutzer {entry.user} hat eine FIBU-Liste gestartet"
                elif entry.protocol_type == "132":
                    line = f"{entry.date}\t{entry.protocol_type}\tIMPSTART\t{entry.user}\tBenutzer {entry.user} hat einen Datenimport gestartet"
                elif entry.protocol_type == "134":
                    line = f"{entry.date}\t{entry.protocol_type}\tWANDLEND\t{entry.user}\tBenutzer {entry.user} hat die Wandlung eines Beleges abgeschlossen"
                elif entry.protocol_type == "136":
                    line = f"{entry.date}\t{entry.protocol_type}\tWANDLKOMPSTART\t{entry.user}\tBenutzer {entry.user} hat eine Komplettwandlung gestartet"
                elif entry.protocol_type == "138":
                    line = f"{entry.date}\t{entry.protocol_type}\tWANDLTEILSTART\t{entry.user}\tBenutzer {entry.user} hat eine Teilwandlung gestartet"
                elif entry.protocol_type == "140":
                    line = f"{entry.date}\t{entry.protocol_type}\tBELPOSDELETE\t{entry.user}\tBenutzer {entry.user} hat eine Belegposition gelöscht"
                elif entry.protocol_type == "142":
                    line = f"{entry.date}\t{entry.protocol_type}\tUPDWANDLTEIL\t{entry.user}\tBenutzer {entry.user} hat einen Beleg für eine Teilwandlung aufbereitet"
                elif entry.protocol_type == "144":
                    line = f"{entry.date}\t{entry.protocol_type}\tBWTOOL4\t{entry.user}\tBenutzer {entry.user} hat eine Wandlung mit bwtool4 durchgeführt"
                elif entry.protocol_type == "146":
                    line = f"{entry.date}\t{entry.protocol_type}\tTRYCATCH\t{entry.user}\tBenutzer {entry.user} hat einen try-Catch-Fehler verursacht"
                elif entry.protocol_type == "148":
                    line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTSTART\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung gestartet"
                elif entry.protocol_type == "150":
                    line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTEND\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung abgeschlossen"
                elif entry.protocol_type == "152":
                    line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTTABSTART\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung/Tabelle gestartet"
                elif entry.protocol_type == "154":
                    line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTTABEND\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung/Tabelle abgeschlossen"

                if line:
                    fp.write(line + "\n")
                    continue

                if entry.status == ProtocolStatus.NEW:
                    line = f"{entry.date}\t{entry.protocol_type}\tNEW\t{entry.user}\tBenutzer {entry.user} hat einen neuen Datensatz im Bereich {entry.protocol_type} angelegt: {entry.index}"
                elif entry.status == ProtocolStatus.CHANGE:
                    line = f"{entry.date}\t{entry.protocol_type}\tCHANGE\t{entry.user}\tBenutzer {entry.user} hat Datensatz {entry.index} im Bereich {entry.protocol_type} geändert:"
                    changes = [f"    {ch.field}: {ch.previous_value.strip()} -> {ch.value.strip()}" for ch in entry.changes if ch.value != ch.previous_value]
                    if changes:
                        changes_lines = "\n".join(changes)
                        line = line + "\n" + changes_lines
                    else:
                        line = line + " Keine erkennbaren Änderungen"
                elif entry.status == ProtocolStatus.DELETE:
                    line = f"{entry.date}\t{entry.protocol_type}\tDELETE\t{entry.user}\tBenutzer {entry.user} hat Datensatz {entry.index} im Bereich {entry.protocol_type} gelöscht"
                elif entry.status == ProtocolStatus.PRINT:
                    line = f"{entry.date}\t{entry.protocol_type}\tPRINT\t{entry.user}\tBenutzer {entry.user} hat Datensatz {entry.index} im Bereich {entry.protocol_type} gedruckt"
                elif entry.status == ProtocolStatus.DELETE_THROUGH_PROCESSING:
                    line = f"{entry.date}\t{entry.protocol_type}\tDELETEWANDL\t{entry.user}\tBenutzer {entry.user} hat Beleg {entry.index} durch Wandlung gelöscht"
                
                if line:
                    fp.write(line + "\n")

    def to_stdout(self):
        for entry in self.load_protocol():
            line = None
            if entry.protocol_type == "000":
                line = f"{entry.date}\t{entry.protocol_type}\tSTART\t{entry.user}\tBenutzer {entry.user} hat sich angemeldet"
            elif entry.protocol_type == "001":
                line = f"{entry.date}\t{entry.protocol_type}\tEND\t{entry.user}\tBenutzer {entry.user} hat sich abgemeldet"
            elif entry.protocol_type == "020":
                line = f"{entry.date}\t{entry.protocol_type}\tKASSESTART\t{entry.user}\tKasse {entry.user} hat sich angemeldet"
            elif entry.protocol_type == "021":
                line = f"{entry.date}\t{entry.protocol_type}\tKASSEEND\t{entry.user}\tKasse {entry.user} hat sich abgemeldet"
            elif entry.protocol_type == "022":
                line = f"{entry.date}\t{entry.protocol_type}\tKASSEDSTART\t{entry.user}\tKasse {entry.user} hat einen Tagesstart durchgeführt"
            elif entry.protocol_type == "023":
                line = f"{entry.date}\t{entry.protocol_type}\tKASSEDEND\t{entry.user}\tKasse {entry.user} hat einen Tagesabschluss durchgeführt"
            elif entry.protocol_type == "031":
                line = f"{entry.date}\t{entry.protocol_type}\tBELCORRECT\t{entry.user}\Bediener {entry.user} hat einen fehlerhaften Beleg automatisch korrigiert: {entry.index}"
            elif entry.protocol_type == "120":
                line = f"{entry.date}\t{entry.protocol_type}\tNOTEDELETE\t{entry.user}\tBenutzer {entry.user} hat Notiztexte gelöscht"
            elif entry.protocol_type == "121":
                line = f"{entry.date}\t{entry.protocol_type}\tGLOBALCANCEL\t{entry.user}\tBenutzer {entry.user} hat einen globalen Abbruch verursacht: {entry.info}"
            elif entry.protocol_type == "122":
                line = f"{entry.date}\t{entry.protocol_type}\tREFERROR\t{entry.user}\tBenutzer {entry.user} hat einen Verweisfehler beim Laden einer Tabelle verursacht"
            elif entry.protocol_type == "123":
                line = f"{entry.date}\t{entry.protocol_type}\tDIFFINDSATZ\t{entry.user}\tBenutzer {entry.user} hat eine Differenz zwischen Index und Satz festgestellt"
            elif entry.protocol_type == "126":
                line = f"{entry.date}\t{entry.protocol_type}\tDUPLBELNR\t{entry.user}\tBenutzer {entry.user} hat versucht eine bestehende Belegnummer erneut anzulegen"
            elif entry.protocol_type == "128":
                line = f"{entry.date}\t{entry.protocol_type}\tWAWILSTART\t{entry.user}\tBenutzer {entry.user} hat eine WAWI-Liste gestartet"
            elif entry.protocol_type == "130":
                line = f"{entry.date}\t{entry.protocol_type}\tFIBULSTART\t{entry.user}\tBenutzer {entry.user} hat eine FIBU-Liste gestartet"
            elif entry.protocol_type == "132":
                line = f"{entry.date}\t{entry.protocol_type}\tIMPSTART\t{entry.user}\tBenutzer {entry.user} hat einen Datenimport gestartet"
            elif entry.protocol_type == "134":
                line = f"{entry.date}\t{entry.protocol_type}\tWANDLEND\t{entry.user}\tBenutzer {entry.user} hat die Wandlung eines Beleges abgeschlossen"
            elif entry.protocol_type == "136":
                line = f"{entry.date}\t{entry.protocol_type}\tWANDLKOMPSTART\t{entry.user}\tBenutzer {entry.user} hat eine Komplettwandlung gestartet"
            elif entry.protocol_type == "138":
                line = f"{entry.date}\t{entry.protocol_type}\tWANDLTEILSTART\t{entry.user}\tBenutzer {entry.user} hat eine Teilwandlung gestartet"
            elif entry.protocol_type == "140":
                line = f"{entry.date}\t{entry.protocol_type}\tBELPOSDELETE\t{entry.user}\tBenutzer {entry.user} hat eine Belegposition gelöscht"
            elif entry.protocol_type == "142":
                line = f"{entry.date}\t{entry.protocol_type}\tUPDWANDLTEIL\t{entry.user}\tBenutzer {entry.user} hat einen Beleg für eine Teilwandlung aufbereitet"
            elif entry.protocol_type == "144":
                line = f"{entry.date}\t{entry.protocol_type}\tBWTOOL4\t{entry.user}\tBenutzer {entry.user} hat eine Wandlung mit bwtool4 durchgeführt"
            elif entry.protocol_type == "146":
                line = f"{entry.date}\t{entry.protocol_type}\tTRYCATCH\t{entry.user}\tBenutzer {entry.user} hat einen try-Catch-Fehler verursacht"
            elif entry.protocol_type == "148":
                line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTSTART\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung gestartet"
            elif entry.protocol_type == "150":
                line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTEND\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung abgeschlossen"
            elif entry.protocol_type == "152":
                line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTTABSTART\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung/Tabelle gestartet"
            elif entry.protocol_type == "154":
                line = f"{entry.date}\t{entry.protocol_type}\tTEMPBELSORTTABEND\t{entry.user}\tBenutzer {entry.user} hat eine temporäre Belegsortierung/Tabelle abgeschlossen"

            if line:
                sys.stdout.write(line + "\n")
                continue

            if entry.status == ProtocolStatus.NEW:
                line = f"{entry.date}\t{entry.protocol_type}\tNEW\t{entry.user}\tBenutzer {entry.user} hat einen neuen Datensatz im Bereich {entry.protocol_type} angelegt: {entry.index}"
            elif entry.status == ProtocolStatus.CHANGE:
                line = f"{entry.date}\t{entry.protocol_type}\tCHANGE\t{entry.user}\tBenutzer {entry.user} hat Datensatz {entry.index} im Bereich {entry.protocol_type} geändert:"
                changes = [f"    {ch.field}: {ch.previous_value.strip()} -> {ch.value.strip()}" for ch in entry.changes if ch.value != ch.previous_value]
                if changes:
                    changes_lines = "\n".join(changes)
                    line = line + "\n" + changes_lines
                else:
                    line = line + " Keine erkennbaren Änderungen"
            elif entry.status == ProtocolStatus.DELETE:
                line = f"{entry.date}\t{entry.protocol_type}\tDELETE\t{entry.user}\tBenutzer {entry.user} hat Datensatz {entry.index} im Bereich {entry.protocol_type} gelöscht"
            elif entry.status == ProtocolStatus.PRINT:
                line = f"{entry.date}\t{entry.protocol_type}\tPRINT\t{entry.user}\tBenutzer {entry.user} hat Datensatz {entry.index} im Bereich {entry.protocol_type} gedruckt"
            elif entry.status == ProtocolStatus.DELETE_THROUGH_PROCESSING:
                line = f"{entry.date}\t{entry.protocol_type}\tDELETEWANDL\t{entry.user}\tBenutzer {entry.user} hat Beleg {entry.index} durch Wandlung gelöscht"
            
            if line:
                sys.stdout.write(line + "\n")