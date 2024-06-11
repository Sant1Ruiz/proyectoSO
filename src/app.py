# Synchrotainer - Proyecto final
# Sistemas operatvios
# Santiago Ruiz Cortes
# Universidad del valle

from flask import Flask, jsonify
import os
import threading
import time
import shutil
import docker
client = docker.from_env()

app = Flask(__name__)

@app.route('/')
def hello_world():
  return {
    'message': 'hola, Mundo!!!'
  }

# permite listar todos los archivos del contenedor <uid> los publicos
@app.route('/storage/<uid>')
def storage(uid):
    container = client.containers.get(uid)
    output = container.exec_run('ls /usr/src/app/sync_files/public', tty=True, stdin=True)
    return jsonify({'resp': output.output.decode('utf-8')})

# permite listar todos los archivos de la red (nube)
@app.route('/public')
def public():
    container_files = os.listdir('/usr/src/app/sync_files/public')
    return jsonify(container_files)

# Descarga un archivo desde el main (nube) al host, usando la carpeta private de la nube que esta compartida con el host
@app.route('/download/<name>')
def download(name):
    try:
        src = '/usr/src/app/sync_files'
        shutil.copy(src+'/public/'+name, src+'/private/'+name)
        return jsonify({'msg': 'El archivo se ha descargado en el host en la carpeta compartida private'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Envia un archivo public del main (nube) al private del contenedor <uid>
@app.route('/upload/<uid>/<name>')
def upload(uid, name):
    container1 = client.containers.get(os.environ.get('HOSTNAME'))
    container2 = client.containers.get(uid)
    bits, stat = container1.get_archive('/usr/src/app/sync_files/public/'+name)
    container2.put_archive('/usr/src/app/sync_files/private/', bits)
    return jsonify({'msg': 'archivo movido a private: '+uid})

# Cada 10 segundo se suben todos los publics de todos los archivos, para asi tener backups automatizados
def auto_backup():
    container_main = client.containers.get(os.environ.get('HOSTNAME'))
    while True:
        contenedores = client.containers.list()
        contenedores = [contenedor for contenedor in contenedores if 'def' in contenedor.name[:3]]
        for contenedor in contenedores:
            if contenedor.name != container_main.name:
                src_dir = '/usr/src/app/sync_files/public/'
                bits, stat = contenedor.get_archive(src_dir)
                container_main.put_archive('/usr/src/app/sync_files/', bits)
        time.sleep(10)

# Crea el hilo de la sincronizacion con la nube
hilo = threading.Thread(target=auto_backup)
hilo.daemon = True
hilo.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)