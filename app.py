import pymysql, datetime, psutil, os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash

app = Flask(__name__)
app.secret_key = 'santa_eufemia_master_key_2026'
LOG_FILE = "/home/pi/proyecto_farmacia/access.log"

def escribir_log(mensaje):
    try:
        with open(LOG_FILE, "a") as f:
            fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{fecha}] {mensaje}\n")
    except Exception as e: pass

def conectar():
    return pymysql.connect(host='127.0.0.1', user='farmacia_user', password='1234', database='farmacia_db', cursorclass=pymysql.cursors.DictCursor)

@app.route('/stats')
def stats():
    return jsonify({"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent})

@app.route('/')
def index():
    db = conectar()
    cur = db.cursor()
    cur.execute("SELECT * FROM Medicamentos WHERE tipo = 'LIBRE'")
    libres = cur.fetchall()
    alertas = [m['nombre'] for m in libres if m['stock'] < 10]
    db.close()
    count = sum(session.get('carrito', {}).values())
    return render_template('index.html', libres=libres, alertas=alertas, carrito_count=count)

@app.route('/add_carrito/<int:id>')
def add_carrito(id):
    carrito = session.get('carrito', {})
    id_str = str(id)
    actual = carrito.get(id_str, 0)
    db = conectar(); cur = db.cursor()
    cur.execute("SELECT nombre FROM Medicamentos WHERE id = %s", (id,))
    producto = cur.fetchone(); db.close()
    if actual >= 3:
        flash(f"⚠️ Máximo 3 unidades de {producto['nombre']}", "error")
        return redirect(url_for('index'))
    carrito[id_str] = actual + 1
    session['carrito'] = carrito
    flash(f"✅ {producto['nombre']} añadido correctamente", "success")
    return redirect(url_for('index'))

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', {})
    items = []
    db = conectar(); cur = db.cursor()
    for id_med, cant in carrito.items():
        cur.execute("SELECT * FROM Medicamentos WHERE id = %s", (id_med,))
        p = cur.fetchone()
        if p: p['cantidad'] = cant; items.append(p)
    db.close()
    return render_template('carrito.html', items=items)

@app.route('/eliminar/<id>')
def eliminar(id):
    carrito = session.get('carrito', {}); id_str = str(id)
    if id_str in carrito:
        del carrito[id_str]
        session['carrito'] = carrito
        flash("Producto quitado de la cesta", "info")
    return redirect(url_for('ver_carrito'))

@app.route('/pagar', methods=['POST'])
def pagar():
    metodo = request.form.get('metodo')
    carrito = session.get('carrito', {})
    if not carrito: return redirect(url_for('index'))
    db = conectar(); cur = db.cursor()
    detalles = ""
    for id_m, cant in carrito.items():
        cur.execute("UPDATE Medicamentos SET stock = stock - %s WHERE id = %s", (cant, id_m))
        cur.execute("SELECT nombre FROM Medicamentos WHERE id = %s", (id_m,))
        detalles += f"{cur.fetchone()['nombre']}(x{cant}) "
    cur.execute("INSERT INTO Pedidos (cliente, detalles, total_items, metodo_pago) VALUES (%s, %s, %s, %s)", ('Venta Libre', detalles, len(carrito), metodo))
    db.commit(); db.close()
    session['carrito'] = {}
    escribir_log(f"VENTA: {detalles} via {metodo}")
    return render_template('resultado.html', mensaje=f"Pago con {metodo} realizado. Gracias.", imagen=None)

@app.route('/escanear', methods=['POST'])
def escanear():
    qr = request.form.get('qr_code')
    db = conectar(); cur = db.cursor()
    cur.execute("SELECT * FROM Pacientes WHERE tarjeta_qr = %s", (qr,))
    paciente = cur.fetchone()
    
    if not paciente:
        res = "❌ ERROR: Tarjeta sanitaria no reconocida."
        img = "error.jpg"
    else:
        cur.execute("SELECT m.nombre, r.estado, r.id FROM Recetas_Activas r JOIN Medicamentos m ON r.medicamento_id = m.id WHERE r.paciente_id = %s", (paciente['id'],))
        receta = cur.fetchone()
        if not receta:
            res = f"ℹ️ HOLA {paciente['nombre_paciente']}. No tiene recetas pendientes."
            img = "info.jpg"
        elif receta['estado'] == 'DISPENSADO':
            res = f"⚠️ AVISO: {paciente['nombre_paciente']}, esta medicación ya fue retirada."
            img = receta['nombre'].split(' ')[0].lower() + ".jpg"
        else:
            cur.execute("UPDATE Recetas_Activas SET estado = 'DISPENSADO' WHERE id = %s", (receta['id'],))
            cur.execute("UPDATE Medicamentos SET stock = stock - 1 WHERE nombre = %s", (receta['nombre'],))
            db.commit()
            escribir_log(f"RECETA: {receta['nombre']} a {paciente['nombre_paciente']}")
            res = f"✅ IDENTIFICADO: {paciente['nombre_paciente']}. Dispensando {receta['nombre']}..."
            img = receta['nombre'].split(' ')[0].lower() + ".jpg"
            
    db.close()
    return render_template('resultado.html', mensaje=res, imagen=img)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
