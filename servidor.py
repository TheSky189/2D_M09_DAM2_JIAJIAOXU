from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Conexión a la base de datos 'jugadores_bd'
db = mysql.connector.connect(
    host="localhost",
    user="root",         # o tu usuario de MySQL
    password="",         # tu contraseña de MySQL
    database="juegos_db"
)
cursor = db.cursor()

# 🔐 Ruta para registrar nuevos usuarios
@app.route('/registro', methods=['POST'])
def registro():
    datos = request.json
    try:
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (datos['usuario'], datos['password']))
        db.commit()
        return jsonify({"status": "success", "message": "Usuario registrado con éxito"})
    except:
        return jsonify({"status": "error", "message": "Usuario ya existe o error de base de datos"}), 400

# 🔑 Ruta para login
@app.route('/autenticar', methods=['POST'])
def autenticar():
    datos = request.json
    usuario = datos['usuario']
    password = datos['password']

    # 1️⃣ Buscar si ya existe
    cursor.execute("SELECT jugador_id FROM usuarios WHERE usuario = %s AND password = %s", (usuario, password))
    resultado = cursor.fetchone()

    if resultado:
        return jsonify({
            "status": "success",
            "message": "Inicio de sesión exitoso",
            "jugador_id": resultado[0]
        })

    # 2️⃣ Si no existe → crear jugador y usuario
    try:
        # Crear nuevo jugador
        cursor.execute("INSERT INTO jugadores (nombre) VALUES (%s)", (usuario,))
        db.commit()
        jugador_id = cursor.lastrowid

        # Crear usuario asociado
        cursor.execute("INSERT INTO usuarios (usuario, password, jugador_id) VALUES (%s, %s, %s)",
                       (usuario, password, jugador_id))
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Usuario nuevo creado automáticamente",
            "jugador_id": jugador_id
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



# 🎮 Insertar una nueva partida (requiere id del jugador)
@app.route('/nueva_partida', methods=['POST'])
def nueva_partida():
    datos = request.json
    cursor.execute("INSERT INTO partidas (jugador_id, puntuacion, tiempo_juego) VALUES (%s, %s, %s)",
                   (datos['jugador_id'], datos['puntuacion'], datos['tiempo_juego']))
    db.commit()
    return jsonify({"status": "success", "message": "Partida guardada"})

# 🏆 Obtener top 10 del ranking
@app.route('/ranking', methods=['GET'])
def ranking():
    cursor.execute("""
        SELECT jugadores.nombre, MAX(partidas.puntuacion) AS mejor_puntuacion, COUNT(partidas.id) AS total_partidas
        FROM jugadores
        JOIN partidas ON jugadores.id = partidas.jugador_id
        GROUP BY jugadores.id
        ORDER BY mejor_puntuacion DESC
        LIMIT 10
    """)
    datos = cursor.fetchall()
    ranking = [{"nombre": row[0], "mejor_puntuacion": row[1], "total_partidas": row[2]} for row in datos]
    return jsonify({"jugadores": ranking})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
