"""Trava o tradutor Firebird->Postgres do Vulcano (db_pg.translate).

Rodar: python test_db_pg.py   (não exige pytest)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_pg import translate


def test_placeholder():
    assert translate("SELECT X FROM T WHERE A=?") == "SELECT X FROM T WHERE A=%s"


def test_first():
    assert translate("SELECT FIRST 1 A FROM T WHERE B=?") == "SELECT A FROM T WHERE B=%s LIMIT 1"


def test_first_100_star():
    assert translate("SELECT FIRST 100 * FROM LCTOCTB") == "SELECT * FROM LCTOCTB LIMIT 100"


def test_fetch_first():
    out = translate("SELECT ID FROM CLIENTE WHERE NOME STARTING WITH ? FETCH FIRST 20 ROWS ONLY")
    assert out == "SELECT ID FROM CLIENTE WHERE NOME LIKE %s || '%%' LIMIT 20"


def test_quoted_identifier_lowercase():
    out = translate('SELECT * FROM LCTOCTB WHERE "CODIGOEMPRESA" = ? ORDER BY DATALCTOCTB DESC')
    assert out == 'SELECT * FROM LCTOCTB WHERE "codigoempresa" = %s ORDER BY DATALCTOCTB DESC'


def test_starting_with_literal():
    out = translate("SELECT 1 FROM T WHERE E=? AND TRIM(C) STARTING WITH '1.1.1'")
    assert out == "SELECT 1 FROM T WHERE E=%s AND TRIM(C) LIKE '1.1.1%%'"


def test_containing_param():
    out = translate("SELECT 1 FROM T WHERE UPPER(H) CONTAINING ? AND E=?")
    assert out == "SELECT 1 FROM T WHERE UPPER(H) ILIKE ('%%' || %s || '%%') AND E=%s"


def test_no_change():
    assert translate("SELECT COUNT(*) FROM PESSOA") == "SELECT COUNT(*) FROM PESSOA"


def test_executemany_insert_null_chave():
    sql = ("INSERT INTO LCTOCTB (CODIGOEMPRESA, CHAVELCTOCTB, DATALCTOCTB) "
           "VALUES (?, ?, CAST(? AS DATE))")
    assert translate(sql) == ("INSERT INTO LCTOCTB (CODIGOEMPRESA, CHAVELCTOCTB, DATALCTOCTB) "
                              "VALUES (%s, %s, CAST(%s AS DATE))")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for f in fns:
        try:
            f(); ok += 1; print("PASS", f.__name__)
        except AssertionError as e:
            print("FALHOU", f.__name__, "->", e)
    print(f"\n{ok}/{len(fns)} testes passaram")
    sys.exit(0 if ok == len(fns) else 1)
