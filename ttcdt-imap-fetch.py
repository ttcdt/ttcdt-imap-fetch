#!/usr/bin/env python3

# ttcdt-imap-fetch
#
# Fetches the content of an IMAP4 server.
#
# This software is released into the public domain.
#
# ttcdt <dev@triptico.com>


import os, imaplib, glob, random, hashlib

def sanitize(s):
    s = s.replace('/', '-')
    s = s.replace('*', '-')
    s = s.replace('@', '-')
    s = s.replace("\n", '-')
    s = s.replace(' ', '-')
    s = s.replace("\r", '')
    s = s.replace('<', '')
    s = s.replace('>', '')
    s = s.replace('[', '')
    s = s.replace(']', '')

    if s != '' and s[0] == '.':
        s = '-' + s[1:]

    return s

def ttcdt_imap_fetch(user, passwd, maildir, host='imap.gmail.com'):
    trash = maildir + '/no-longer-on-server'

    try:
        os.mkdir(maildir)
        os.mkdir(trash)
        os.mkdir(trash + '/cur')
        os.mkdir(trash + '/tmp')
        os.mkdir(trash + '/new')
    except:
        pass

    I = imaplib.IMAP4_SSL(host)
    I.login(user, passwd)

    typ, folders = I.list()

    i = random.randrange(len(folders))
    folders = folders[i:] + folders[0:i]

    for f in folders:
        # extract folder name
        f_name = f.decode('utf-8').split(' "/" ')[1].replace('"', '')

        print("INFO : Checking", f_name)

        I.select(f_name)

        folder_ok = True

        try:
            # pick all information in one humungous packet
            typ, raw_msgs = I.fetch('1:*', '(BODY[HEADER.FIELDS (Message-Id Date)])')

        except:
            print("INFO : Skipping", f_name)
            folder_ok = False

        if folder_ok:
            s_fname = maildir + '/' + sanitize(f_name)

            # create the folders
            try:
                os.mkdir(s_fname)
                os.mkdir(s_fname + '/cur')
                os.mkdir(s_fname + '/tmp')
                os.mkdir(s_fname + '/new')
            except:
                pass

            # get the msg_ids of the already downloaded messages
            on_disk = set([e.split('/')[-1] for e in glob.glob(s_fname + '/cur/*')])

            # get the list of local folders
            on_disk_folders = glob.glob(maildir + '/*/cur')

            to_download = []

            for raw_msg in raw_msgs:
                if not isinstance(raw_msg, tuple):
                    continue

                oid    = raw_msg[0].decode('utf-8').split(" ", 1)[0]
                hdrs_l = raw_msg[1].decode('utf-8').split("\r\n")

                hdrs = {}
                for h in hdrs_l:
                    h = h.split(': ')
                    if len(h) == 2:
                        hdrs[h[0].lower()] = h[1]

                msg_id = hdrs.get('message-id') or hdrs.get('date') or ''

                if msg_id == '':
                    # no valid identifier: use md5 of everything
                    typ, data = I.fetch(oid, '(RFC822)')
                    m = hashlib.md5()
                    m.update(data[0][1])
                    msg_id = m.hexdigest()

                if msg_id == '':
                    print("ERROR:", f_name, "empty msg_id (%s)" % oid)
                else:
                    msg_id = sanitize(msg_id) + ":2,S"

                    if msg_id in on_disk:
                        # already here; done with it
#                        print("SKIP :", msg_id)
                        on_disk.remove(msg_id)
                    else:
                        # is this message on disk but on another folder?
                        msg_file = s_fname + '/cur/' + msg_id
                        link_dst = ''
                        for o_fldr in on_disk_folders:
                            link_dst = o_fldr + '/' + msg_id

                            if os.access(link_dst, os.F_OK):
                                break
                            else:
                                link_dst = ''

                        if link_dst != '':
                            if os.access(msg_file, os.F_OK):
#                                print("ERROR:", "file exists", msg_file)
                                pass
                            else:
                                print("LINK :", f_name, "(%s)" % (oid))
                                os.link(link_dst, msg_file)

                        else:
                            # full download needed
                            to_download.append([oid, msg_id])

            print("INFO : Processing", f_name,
                "(store: %d, trash: %d)" % (len(to_download), len(on_disk)))

            cnt = 1

            # now iterate to_download asking for the bodies
            for msg in to_download:
                oid    = msg[0]
                msg_id = msg[1]

                typ, data = I.fetch(oid, '(RFC822)')

                print("STORE:", f_name, "(%d/%d)" % (cnt, len(to_download)))

                with open(s_fname + '/cur/' + msg_id, "wb") as f:
                    f.write(data[0][1].replace(b"\r", b""))

                cnt += 1

            cnt = 1

            # sack all messages no longer on the server
            for msg_id in on_disk:
                try:
                    src = s_fname + '/cur/' + msg_id
                    dst = trash + '/cur/' + sanitize(f_name) + '@' + msg_id
                    os.rename(src, dst)

                    print("TRASH:", f_name, "(%d/%d)" % (cnt, len(on_disk)))
                except:
                    print("ERROR: trashing ", msg_id)

                cnt += 1


if __name__ == "__main__":
    import sys, getpass

    print("ttcdt-imap-fetch 1.01 - Fetches the content of an IMAP4 server")
    print("ttcdt <dev@triptico.com>\n")

    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print("Usage: ttcdt-imap-fetch.py {user} {maildir path} [{host}]")
    else:
        user    = sys.argv[1]
        passwd  = getpass.getpass("Password for '%s': " % user)
        maildir = sys.argv[2]

        if len(sys.argv) == 4:
            host = sys.argv[3]
        else:
            host = "imap.gmail.com"

        ttcdt_imap_fetch(user, passwd, maildir, host)
