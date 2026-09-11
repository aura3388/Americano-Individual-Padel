import base64
import json
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Americano Padel Tournaments", layout="wide")

# Inicializar session_state si no existe
if "players" not in st.session_state:
    st.session_state["players"] = []
if "matches" not in st.session_state:
    st.session_state["matches"] = []
if "tournament_started" not in st.session_state:
    st.session_state["tournament_started"] = False

# Sistema de persistencia automática ultraseguro en la URL
def save_to_url():
    try:
        state_data = {
            "players": st.session_state.get("players", []),
            "matches": st.session_state.get("matches", []),
            "tournament_started": st.session_state.get("tournament_started", False)
        }
        json_str = json.dumps(state_data)
        # Usamos urlsafe para evitar errores con caracteres especiales en el navegador
        b64_str = base64.urlsafe_b64encode(json_str.encode()).decode()
        st.query_params["state"] = b64_str
    except Exception:
        pass

def load_from_url():
    if "state" in st.query_params and not st.session_state.get("loaded_from_url", False):
        try:
            b64_str = st.query_params["state"]
            json_str = base64.urlsafe_b64decode(b64_str.encode()).decode()
            state_data = json.loads(json_str)
            st.session_state["players"] = state_data.get("players", [])
            st.session_state["matches"] = state_data.get("matches", [])
            st.session_state["tournament_started"] = state_data.get("tournament_started", False)
            
            # Sincronizar los widgets con los datos recuperados
            for m in st.session_state["matches"]:
                m_id = m["id"]
                st.session_state[f"s1_{m_id}"] = m["score1"]
                st.session_state[f"s2_{m_id}"] = m["score2"]
                st.session_state[f"st_{m_id}"] = m["status"]
                
            st.session_state["loaded_from_url"] = True
        except Exception:
            pass

load_from_url()

st.title("🏆 Gestor Americano Individual de Pádel")

# Interfaz de configuración de jugadoras
if not st.session_state["tournament_started"]:
    st.subheader("Registro de Jugadoras")
    player_input = st.text_area(
        "Ingresa los nombres de las jugadoras (debe ser múltiplo de 4, ej: 4, 8, 12... uno por línea):",
        value="\n".join(st.session_state["players"]) if st.session_state["players"] else ""
    )
    
    if st.button("Generar Calendario y Comenzar Torneo"):
        names = [n.strip() for n in player_input.split("\n") if n.strip()]
        if len(names) < 4 or len(names) % 4 != 0:
            st.error("El número total de jugadoras debe ser múltiplo de 4 (ej. 4, 8, 12, 16) para asegurar la rotación perfecta.")
        else:
            st.session_state["players"] = names
            
            generated_matches = []
            match_id = 1
            
            for r in range(len(names) // 2):
                p = names[:]
                if r > 0:
                    p = [p[0]] + p[1:][r:] + p[1:r]
                
                for i in range(0, len(p), 4):
                    if i + 3 < len(p):
                        team1_p1 = p[i]
                        team1_p2 = p[i+1]
                        team2_p1 = p[i+2]
                        team2_p2 = p[i+3]
                        
                        generated_matches.append({
                            "id": match_id,
                            "round": r + 1,
                            "team1": f"{team1_p1} / {team1_p2}",
                            "team2": f"{team2_p1} / {team2_p2}",
                            "score1": 0,
                            "score2": 0,
                            "status": "Programado"
                        })
                        match_id += 1

            st.session_state["matches"] = generated_matches
            st.session_state["tournament_started"] = True
            
            # Inicializar keys de los widgets
            for m in generated_matches:
                st.session_state[f"s1_{m['id']}"] = 0
                st.session_state[f"s2_{m['id']}"] = 0
                st.session_state[f"st_{m['id']}"] = "Programado"

            save_to_url()
            st.rerun()

else:
    st.subheader("📋 Control de Partidos y Resultados")
    
    if st.button("Reiniciar Torneo / Cambiar Jugadoras"):
        st.session_state["tournament_started"] = False
        st.session_state["players"] = []
        st.session_state["matches"] = []
        if "state" in st.query_params:
            del st.query_params["state"]
        st.rerun()

    matches = st.session_state["matches"]
    
    for idx, match in enumerate(matches):
        status = match["status"]
        bg_style = "background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin-bottom: 15px;" if status == "Programado" else "background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 15px;"
        
        with st.container():
            st.markdown(f"<div style='{bg_style}'>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**Partido {match['id']} (Ronda {match['round']})**")
                st.text(f"Pareja 1: {match['team1']}")
            with col2:
                st.text(f"Pareja 2: {match['team2']}")
            with col3:
                new_score1 = st.number_input("P1", min_value=0, max_value=10, value=match["score1"], key=f"s1_{match['id']}")
                new_score2 = st.number_input("P2", min_value=0, max_value=10, value=match["score2"], key=f"s2_{match['id']}")
            with col4:
                new_status = st.selectbox("Estado", ["Programado", "En juego", "Finalizado"], index=["Programado", "En juego", "Finalizado"].index(status), key=f"st_{match['id']}")
            
            # Actualizar datos si cambian y forzar guardado en URL
            if new_score1 != match["score1"] or new_score2 != match["score2"] or new_status != match["status"]:
                st.session_state["matches"][idx]["score1"] = new_score1
                st.session_state["matches"][idx]["score2"] = new_score2
                st.session_state["matches"][idx]["status"] = new_status
                save_to_url()
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

    # Tabla de Posiciones general
    st.subheader("📊 Tabla de Posiciones")
    scores_dict = {p: 0 for p in st.session_state["players"]}
    
    for m in matches:
        if m["status"] == "Finalizado":
            t1_names = m["team1"].split(" / ")
            t2_names = m["team2"].split(" / ")
            
            for p in t1_names:
                if p in scores_dict:
                    scores_dict[p] += m["score1"]
            for p in t2_names:
                if p in scores_dict:
                    scores_dict[p] += m["score2"]
                    
    df_scores = pd.DataFrame(list(scores_dict.items()), columns=["Jugadora", "Puntos Totales"])
    df_scores = df_scores.sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
    st.table(df_scores)
