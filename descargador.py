#!/usr/bin/env python

from datetime import date, timedelta
from requests import get
from cStringIO import StringIO
import Image

from Queue import Queue
from threading import Thread
from os.path import exists as existe


def generarURL_thumbnail(fecha):
    """Arma la URL para descargar el thumbnail de la tapa"""
    # print "Generando thumbnail url para %s-%s-%s" % (fecha.day, fecha.month, fecha.year)
    t_url = "{3}/{0}/{1:02d}/{2:02d}/{0}{1:02d}{2:02d}_thumb.jpg".format(
        fecha.year, fecha.month, fecha.day, base_url)
    return t_url


def generarURL_large(fecha):
    """Arma la URL para descargar la tapa en alta resolucion"""
    # print "Generando large url para %s-%s-%s" % (fecha.day, fecha.month, fecha.year)
    l_url = "{3}/{0}/{1:02d}/{2:02d}/{0}{1:02d}{2:02d}.jpg".format(
        fecha.year, fecha.month, fecha.day, base_url)
    return l_url


def _descarga(url):
    """Descarga datos a un StringIO mediante la libreria Requests"""
    descarga = get(url)

    if descarga.status_code != 200: return
    # print "Descargando %s [%s]" % (url, descarga.status_code)

    try:
        print "Descargados %d kB de %s" % (len(descarga.content)/1024, url)
        fh = StringIO(descarga.content)
        return fh
    except Exception, e:
        print "Error descargando %s:\n%s\n" % (url, e)


def descargarTapas(i):
    """La funcion para el trabajador que procesa las url que caen en la Queue"""
    while True:
        descarga = descargas.get()

        if descarga:
            datos = _descarga(descarga)
            if datos is None:
                descargas.task_done()

            nombre = descarga.split('/')[-1]
            print "Procesando %s" % nombre
            try:
                imagen = Image.open(datos)
                imagen = imagen.resize([int(s * 0.5) for s in imagen.size])
                imagen.save(nombre, quality=75, optimize=True, progressive=True)

            except Exception, e:
                print "Error convirtiendo imagen %s: %s" % (nombre, e)

            finally:
                descargas.task_done()


if __name__ == "__main__":
    base_url = "http://tapas.clarin.com/tapa"  # /1946/01/03/19460103_thumb.jpg
    fecha = date.today()
    dia = timedelta(days=1)

    descargas = Queue()

    print "Generando URLs para descargar imagenes..."
    while True:
        l = generarURL_large(fecha)

        if not existe(l.split('/')[-1]):  # Si ya existe, paso al siguiente
            descargas.put(l)

        fecha = fecha-dia

        if fecha.year == 1940:
            break

    print "Iniciando trabajadores..."
    for i in range(16):
        worker = Thread(target=descargarTapas, args=(i,))
        worker.setDaemon(True)
        worker.start()

    descargas.join()
