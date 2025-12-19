from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import sqlite3
import pandas as pd
import io
from datetime import datetime

app = FastAPI(title="Gestión Docente Panamá")

# Base de datos
DATABASE = "gestion.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            apellidos TEXT,
            nombres TEXT,
            cedula TEXT,
            grupo TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def home():
    return {"app": "Gestión Docente", "formula": "[(puntos/totales)×4]+1"}

@app.get("/calcular/{puntos}/{total}")
def calcular_nota(puntos: float, total: float = 100.0):
    if total <= 0:
        return {"error": "Total debe ser > 0"}
    
    nota = ((puntos / total) * 4) + 1
    nota = max(1.0, min(5.0, round(nota, 1)))
    
    return {
        "puntos": puntos,
        "total": total,
        "nota": nota,
        "formula": f"[({puntos}/{total})×4]+1"
    }

@app.post("/importar-csv")
async def importar_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO estudiantes 
                (codigo, apellidos, nombres, cedula, grupo)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                str(row.get('codigo', '')),
                str(row.get('apellidos', '')),
                str(row.get('nombres', '')),
                str(row.get('cedula', '')),
                str(row.get('grupo', '10A'))
            ))
        
        conn.commit()
        conn.close()
        
        return {"mensaje": f"Importados {len(df)} estudiantes"}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/estudiantes")
def obtener_estudiantes():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"estudiantes": estudiantes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
