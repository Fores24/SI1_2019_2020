# -*- coding: utf-8 -*-

import os
import sys, traceback, time
import psycopg2

from sqlalchemy import create_engine, exc

# configurar el motor de sqlalchemy
db_engine = create_engine("postgresql://alumnodb:alumnodb@localhost/si1", echo=False, execution_options={"autocommit":False})

def dbConnect():
    return db_engine.connect()

def dbCloseConnect(db_conn):
    db_conn.close()
########################################################################################


########################################################################################

def _query_loop(db_conn, query_str_wo_thh, iumbral, iintervalo, break0, niter):
    # Query result array for each threshold
    dbr=[]

    for i in range(niter):
        query_str = query_str_wo_thh+", "+str(iumbral)+")"
        ret = db_conn.execute(query_str)
        ret_list = list(ret)

        cont = ret_list[0][0]
        dbr.append({"umbral":iumbral,"contador":cont})

        ret.close()

        if break0 and not int(ret_list[0][0]):
            break

        iumbral += iintervalo

    return dbr

def getListaCliMes(db_conn, mes, anio, iumbral, iintervalo, use_prepare, break0, niter):

    # Query result array for each threshold
    dbr=[]

    if use_prepare:
        queryplan_str = "PREPARE clientesDistintosPlan (int, int, numeric) AS "+\
                    "SELECT * FROM clientesDistintos($1, $2, $3)"
        ret_prep = db_conn.execute(queryplan_str)
        ret_prep.close()

        query_str_wo_thh = "EXECUTE clientesDistintosPlan("+str(mes)+", "+str(anio)
        dbr = _query_loop(db_conn, query_str_wo_thh, iumbral, iintervalo, break0, niter)

        queryplan_str = "DEALLOCATE PREPARE clientesDistintosPlan"
        ret_prep = db_conn.execute(queryplan_str)
        ret_prep.close()

    else:
        query_str_wo_thh = "SELECT * FROM clientesDistintos("+str(mes)+", "+str(anio)
        dbr = _query_loop(db_conn, query_str_wo_thh, iumbral, iintervalo, break0, niter)

    return dbr
########################################################################################


########################################################################################

query_delInventory = "UPDATE inventory " +\
                     "SET sales=sales-orderdetail.quantity " +\
                     "FROM orderdetail, orders " +\
                     "WHERE inventory.prod_id=orderdetail.prod_id AND " +\
                     "orderdetail.orderid=orders.orderid AND " +\
                     "orders.customerid="
query_delOrderdetail = "DELETE FROM orderdetail " +\
                       "USING orders " +\
                       "WHERE orderdetail.orderid=orders.orderid AND " +\
                       "orders.customerid="
query_delOrders = "DELETE FROM orders " +\
                  "WHERE orders.customerid="
query_delCustomers = "DELETE FROM customers " +\
                     "WHERE customerid="

def _parse_error_message(exc_str):
    ret = ""
    ind = exc_str.find("\n")
    ret = exc_str[:ind]
    return ret


def _delCustomerExec(customerid, bFallo, duerme, bCommit):
    dbr = []
    db_conn = dbConnect()

    try:
        # Init transaction BEGIN
        ret = db_conn.execute("BEGIN")
        ret.close()
        dbr.append({"safe":"BEGIN transaction"})
        # Updating inventory
        ret = db_conn.execute(query_delInventory+str(customerid))
        ret.close()
        dbr.append({"safe":"Updated inventory entries for customerid="+str(customerid)})

        if bFallo:
        # Forcing database error and rolling back
            # Deleting orders data (WITHOUT DELETING orderdetail data before!)
            ret = db_conn.execute(query_delOrders+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orders entries for customerid="+str(customerid)})
            # Deleting orderdetail data
            ret = db_conn.execute(query_delOrderdetail+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orderdetail entries for customerid="+str(customerid)})
            # Deleting customer data
            ret = db_conn.execute(query_delCustomers+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted customers entry for customerid="+str(customerid)})

        else:
        # Good transaction
            # Deleting orderdetail data
            ret = db_conn.execute(query_delOrderdetail+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orderdetail entries for customerid="+str(customerid)})
            # Deleting orders data
            ret = db_conn.execute(query_delOrders+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orders entries for customerid="+str(customerid)})
            # Deleting customer data
            ret = db_conn.execute(query_delCustomers+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted customers entry for customerid="+str(customerid)})

    except Exception as e:
        ret = db_conn.execute("ROLLBACK")
        ret.close()
        dbr.append({"safe":"An Error ocurred during transaction. Rolling back. "+_parse_error_message(str(e))})

    else:
        ret = db_conn.execute("COMMIT")
        ret.close()
        dbr.append({"safe":"Customer data deleted successfully"})

    dbCloseConnect(db_conn)
    return dbr

def _delCustomerAlc(customerid, bFallo, duerme, bCommit):
    dbr = []
    db_conn = dbConnect()

    try:
        # Init transaction BEGIN
        trans = db_conn.begin()
        dbr.append({"safe":"BEGIN transaction"})
        # Updating inventory
        ret = db_conn.execute(query_delInventory+str(customerid))
        ret.close()
        dbr.append({"safe":"Updated inventory entries for customerid="+str(customerid)})

        if bFallo:
        # Forcing database error and rolling back
            # Deleting orders data (WITHOUT DELETING orderdetail data before!)
            ret = db_conn.execute(query_delOrders+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orders entries for customerid="+str(customerid)})
            # Deleting orderdetail data
            ret = db_conn.execute(query_delOrderdetail+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orderdetail entries for customerid="+str(customerid)})
            # Deleting customer data
            ret = db_conn.execute(query_delCustomers+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted customers entry for customerid="+str(customerid)})

        else:
        # Good transaction
            # Deleting orderdetail data
            ret = db_conn.execute(query_delOrderdetail+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orderdetail entries for customerid="+str(customerid)})
            # Deleting orders data
            ret = db_conn.execute(query_delOrders+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted orders entries for customerid="+str(customerid)})
            # Deleting customer data
            ret = db_conn.execute(query_delCustomers+str(customerid))
            ret.close()
            dbr.append({"safe":"Deleted customers entry for customerid="+str(customerid)})

    except Exception as e:
        trans.rollback()
        dbr.append({"safe":"An Error ocurred during transaction. Rolling back. "+_parse_error_message(str(e))})
    else:
        trans.commit()
        dbr.append({"safe":"Customer data deleted successfully"})

    dbCloseConnect(db_conn)
    return dbr

def delCustomer(customerid, bFallo, bSQL, duerme, bCommit):

    # Array de trazas a mostrar en la página
    dbr=[]

    # TODO: Ejecutar consultas de borrado
    # - ordenar consultas según se desee provocar un error (bFallo True) o no
    # - ejecutar commit intermedio si bCommit es True
    # - usar sentencias SQL ('BEGIN', 'COMMIT', ...) si bSQL es True
    # - suspender la ejecución 'duerme' segundos en el punto adecuado para forzar deadlock
    # - ir guardando trazas mediante dbr.append()

    if bSQL:
        dbr = _delCustomerExec(customerid, bFallo, duerme, bCommit)
    else:
        dbr = _delCustomerAlc(customerid, bFallo, duerme, bCommit)

    return dbr
########################################################################################


########################################################################################

def getMovies(anio):
    # conexion a la base de datos
    db_conn = db_engine.connect()

    query="select movietitle from imdb_movies where year = '" + anio + "'"
    resultproxy=db_conn.execute(query)

    a = []
    for rowproxy in resultproxy:
        d={}
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for tup in rowproxy.items():
            # build up the dictionary
            d[tup[0]] = tup[1]
        a.append(d)

    resultproxy.close()

    db_conn.close()

    return a
########################################################################################


########################################################################################

def getCustomer(username, password):
    # conexion a la base de datos
    db_conn = db_engine.connect()

    query="select * from customers where username='" + username + "' and password='" + password + "'"
    res=db_conn.execute(query).first()

    db_conn.close()

    if res is None:
        return None
    else:
        return {'firstname': res['firstname'], 'lastname': res['lastname']}
########################################################################################



if __name__ == "__main__":
    # db_conn, query_str_wo_thh, iumbral, iintervalo, break0, niter
    #print(getListaCliMes(dbConnect(), 4, 2015, 100, 50, 1, 1, 1000))

    # customerid, bFallo, bSQL, duerme, bCommit
    print(delCustomer(4, 1, 1, 0, 0))
    print("")
    print(delCustomer(4, 0, 1, 0, 0))
    print("")
    print(delCustomer(5, 1, 0, 0, 0))
    print("")
    print(delCustomer(5, 0, 0, 0, 0))
