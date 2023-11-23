#!/usr/bin/python
# uses unwrap code from: niels at teusink net / blog.teusink.net
# requires Oracle Instant Client and cx-oracle (http://cx-oracle.sourceforge.net/)
# make sure python 3.x is used to run this script and ORACLE_HOME is set

import os, shutil
import re, base64, zlib
import cx_Oracle
import logging
import configparser
import argparse

# logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# config parser
config = configparser.ConfigParser()
config.read('config.ini') # read db credentials from a config file

# command line arg parser
parser = argparse.ArgumentParser(description='oracle db object dumper')
parser.add_argument('--dump_path', help='directory to dump the objects', default='DDL')
parser.add_argument('--object_types', nargs='+', help='list of object types to dump', default=["PACKAGE", "PROCEDURE", "TRIGGER"])
parser.add_argument('--users', nargs='+', help='list of db users', default=[])
args = parser.parse_args()

# decode and decompress a b64 encoded string
def decode_base64_package(base64str):
    """
    decode and decompress a base64 encoded string
    """
    charmap = [0x3d, 0x65, 0x85, 0xb3, 0x18, 0xdb, 0xe2, 0x87, 0xf1, 0x52, 0xab, 0x63, 0x4b, 0xb5, 0xa0, 0x5f, 0x7d, 0x68, 0x7b, 0x9b, 0x24, 0xc2, 0x28, 0x67, 0x8a, 0xde, 0xa4, 0x26, 0x1e, 0x03, 0xeb, 0x17, 0x6f, 0x34, 0x3e, 0x7a, 0x3f, 0xd2, 0xa9, 0x6a, 0x0f, 0xe9, 0x35, 0x56, 0x1f, 0xb1, 0x4d, 0x10, 0x78, 0xd9, 0x75, 0xf6, 0xbc, 0x41, 0x04, 0x81, 0x61, 0x06, 0xf9, 0xad, 0xd6, 0xd5, 0x29, 0x7e, 0x86, 0x9e, 0x79, 0xe5, 0x05, 0xba, 0x84, 0xcc, 0x6e, 0x27, 0x8e, 0xb0, 0x5d, 0xa8, 0xf3, 0x9f, 0xd0, 0xa2, 0x71, 0xb8, 0x58, 0xdd, 0x2c, 0x38, 0x99, 0x4c, 0x48, 0x07, 0x55, 0xe4, 0x53, 0x8c, 0x46, 0xb6, 0x2d, 0xa5, 0xaf, 0x32, 0x22, 0x40, 0xdc, 0x50, 0xc3, 0xa1, 0x25, 0x8b, 0x9c, 0x16, 0x60, 0x5c, 0xcf, 0xfd, 0x0c, 0x98, 0x1c, 0xd4, 0x37, 0x6d, 0x3c, 0x3a, 0x30, 0xe8, 0x6c, 0x31, 0x47, 0xf5, 0x33, 0xda, 0x43, 0xc8, 0xe3, 0x5e, 0x19, 0x94, 0xec, 0xe6, 0xa3, 0x95, 0x14, 0xe0, 0x9d, 0x64, 0xfa, 0x59, 0x15, 0xc5, 0x2f, 0xca, 0xbb, 0x0b, 0xdf, 0xf2, 0x97, 0xbf, 0x0a, 0x76, 0xb4, 0x49, 0x44, 0x5a, 0x1d, 0xf0, 0x00, 0x96, 0x21, 0x80, 0x7f, 0x1a, 0x82, 0x39, 0x4f, 0xc1, 0xa7, 0xd7, 0x0d, 0xd1, 0xd8, 0xff, 0x13, 0x93, 0x70, 0xee, 0x5b, 0xef, 0xbe, 0x09, 0xb9, 0x77, 0x72, 0xe7, 0xb2, 0x54, 0xb7, 0x2a, 0xc7, 0x73, 0x90, 0x66, 0x20, 0x0e, 0x51, 0xed, 0xf8, 0x7c, 0x8f, 0x2e, 0xf4, 0x12, 0xc6, 0x2b, 0x83, 0xcd, 0xac, 0xcb, 0x3b, 0xc4, 0x4e, 0xc0, 0x69, 0x36, 0x62, 0x02, 0xae, 0x88, 0xfc, 0xaa, 0x42, 0x08, 0xa6, 0x45, 0x57, 0xd3, 0x9a, 0xbd, 0xe1, 0x23, 0x8d, 0x92, 0x4a, 0x11, 0x89, 0x74, 0x6b, 0x91, 0xfb, 0xfe, 0xc9, 0x01, 0xea, 0x1b, 0xf7, 0xce]
    try:
        base64dec = base64.decodebytes(bytes(base64str, "ASCII"))[20:]
        decoded = bytearray(len(base64dec))
        for i in range(len(base64dec)):
            decoded[i] = charmap[base64dec[i]]
        return zlib.decompress(decoded).decode()
    except Exception as e:
        logging.error(f"Error in decoding: {e}")
        return None

# check if DDL is wrapped
def is_wrapped(ddl):
    """
    check if the DDL is wrapped
    """
    return ddl and ddl.splitlines()[0].find("wrapped") != -1


def unwrap(ddl):
    """
    unwrap the wrapped DDL
    """
    lines = ddl.splitlines(True)
    for i, line in enumerate(lines):
        matches = re.compile(r"^[0-9a-f]+ ([0-9a-f]+)$").match(line)
        if matches:
            base64len = int(matches.groups()[0], 16)
            base64str = ''.join(lines[i+1:i+1+base64len]).replace("\n", "")
            return decode_base64_package(base64str)
    return None


def save_ddl(path_to_save, ddl):
    """
    save the DDL to a file and unwrap if necessary
    """
    try:
        unwrapped_ddl = unwrap(ddl) if is_wrapped(ddl) else ddl
        if unwrapped_ddl is None:
            logging.error(f"failed to dump wrapped object: {path_to_save}")
            return

        with open(path_to_save, "w", encoding="UTF-8") as fd:
            fd.write(unwrapped_ddl)
    except Exception as e:
        logging.error(f"error saving file {path_to_save}: {e}")


def main():
    """
    main function to connect to db, retrieve and save DDLs
    """
    try:
        # db connection
        ezconnectinfo = config.get('database', 'connection_string')
        con = cx_Oracle.connect(ezconnectinfo)
        logging.info("connected to the db!")

        cur = con.cursor()

        # fetch users
        if not args.users:
            cur.execute("SELECT USERNAME FROM DBA_USERS")
            users = [row[0] for row in cur]
        else:
            users = args.users

        # fetch and save DDLs
        for username in users:
            logging.info(f"dumping objects for owner: {username}")
            current_owner_path = os.path.join(args.dump_path, username)
            if os.path.exists(current_owner_path):
                shutil.rmtree(current_owner_path)
            os.makedirs(current_owner_path)

            object_types = "','".join(args.object_types)
            cur.execute("SELECT OBJECT_NAME, OBJECT_TYPE FROM DBA_OBJECTS WHERE OWNER = :username AND OBJECT_TYPE IN (:object_types)", {'username': username, 'object_types': object_types})
            for objname, objtype in cur:
                ddl_query = "SELECT TEXT FROM DBA_SOURCE WHERE NAME = :objname AND TYPE = :objtype AND OWNER = :username ORDER BY LINE"
                cur2 = con.cursor()
                cur2.execute(ddl_query, {'objname': objname, 'objtype': objtype, 'username': username})
                ddl = ''.join([text[0] for text in cur2])
                cur2.close()

                safe_name = f"{objname.replace(os.sep, '_').replace(' ', '_')}_{objtype.replace(' ', '_')}.sql"
                logging.info(f"saving file: {path_to_save}")
                save_ddl(path_to_save, ddl)

        cur.close()
        con.close()
    except Exception as e:
        logging.error(f"error in main function: {e}")

if __name__ == "__main__":
    main()
