PROJ=ttcdt-imap-fetch.py
PREFIX=/usr/local/bin

all:
	@echo "Run make install to install."

install:
	install -m 755 $(PROJ) $(PREFIX)/$(PROJ)

uninstall:
	rm -f $(PREFIX)/$(PROJ)

dist:
	rm -f ttcdt-imap-fetch.tar.gz && cd .. && \
		tar czvf ttcdt-imap-fetch/ttcdt-imap-fetch.tar.gz ttcdt-imap-fetch/*

clean:
	rm -f *.tar.gz *.asc
