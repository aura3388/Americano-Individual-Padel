import streamlit as st
import pandas as pd
import itertools
import random

st.set_page_config(page_title="LD.SPORT - Gestor Integral de Torneos", layout="wide")

# ==========================================
# GESTIÓN DE ESTADO Y PERSISTENCIA (SESSION STATE)
# ==========================================
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False
if "admin_pin" not in st.session_state:
    st.session_state.admin_pin = "1234"
if "num_groups" not in st.session_state:
    st.session_state.num_groups = 4
if "courts_count" not in st.session_state:
    st.session_state.courts_count = 4
if "players" not in st.session_state:
    st.session_state.players = []
if "matches" not in st.session_state:
    st.session_state.matches = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Ranking"
if "active_standings_group" not in st.session_state:
    st.session_state.active_standings_group = "A"

# ==========================================
# BARRA LATERAL (CONFIGURACIÓN Y AUTENTICACIÓN)
# ==========================================
st.sidebar.title("⚡ LD.SPORT Admin")

pin_input = st.sidebar.text_input("PIN de Administrador", type="password")
if pin_input == st.session_state.admin_pin:
    st.session_state.admin_auth = True
    st.sidebar.success("Modo Administrador Activo")
elif pin_input != "":
    st.sidebar.error("PIN incorrecto")

if st.session_state.admin_auth:
    if st.sidebar.button("🔒 Bloquear Administrador"):
        st.session_state.admin_auth = False
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("⚙️ Configuración Global")
new_pin_setup = st.sidebar.text_input("Cambiar PIN de Admin", type="password")
if st.sidebar.button("Guardar Nuevo PIN") and new_pin_setup:
    if len(new_pin_setup) >= 3:
        st.session_state.admin_pin = new_pin_setup
        st.sidebar.success("PIN actualizado con éxito.")
    else:
        st.sidebar.warning("El PIN debe tener al menos 3 caracteres.")

# ==========================================
# TÍTULO PRINCIPAL Y NAVEGACIÓN DE PESTAÑAS
# ==========================================
st.title("🎾 LD.SPORT - Torneo Americano de Pádel Optimizado")

tabs = ["📊 Ranking por Grupos", "🔍 Jugadoras y Verificación", "📅 Fixture y Resultados", "⚙️ Configuración y Sorteo"]
selected_tab = st.radio("Navegación", tabs, horizontal=True, label_visibility="collapsed")

# Utilidades de Grupos
def get_group_letter(index):
    return chr(65 + index)

def assign_random_group():
    total_g = st.session_state.num_groups
    group_counts = {get_group_letter(i): 0 for i in range(total_g)}
    for p in st.session_state.players:
        g = p.get("group", "A")
        if g in group_counts:
            group_counts[g] += 1
            
    for i in range(total_g):
        g_key = get_group_letter(i)
        if group_counts[g_key] < 4:
            return g_key
            
    min_size = min(group_counts.values())
    for i in range(total_g):
        g_key = get_group_letter(i)
        if group_counts[g_key] == min_size:
            return g_key
    return "A"

# Generador optimizado con heurística estricta de rivales y compañeras
def generate_americano_schedule(group_players, group_name, start_match_id, courts_count):
    players = list(group_players)
    N = len(players)
    if N < 4:
        return []
    
    all_pairs = list(itertools.combinations(players, 2))
    
    def solve():
        for _ in range(1000):
            rem = list(all_pairs)
            random.shuffle(rem)
            matches = []
            rivals_count = {p: set() for p in players}
            
            possible = True
            while rem:
                t1 = rem.pop(0)
                p1, p2 = t1
                valid_indices = []
                for i, t2 in enumerate(rem):
                    q1, q2 = t2
                    if q1 != p1 and q1 != p2 and q2 != p1 and q2 != p2:
                        valid_indices.append(i)
                
                if not valid_indices:
                    possible = False
                    break
                
                best_i = valid_indices[0]
                best_score = -1
                for i in valid_indices:
                    q1, q2 = rem[i]
                    score = 0
                    if q1 not in rivals_count[p1]: score += 1
                    if q2 not in rivals_count[p1]: score += 1
                    if q1 not in rivals_count[p2]: score += 1
                    if q2 not in rivals_count[p2]: score += 1
                    if score > best_score:
                        best_score = score
                        best_i = i
                        
                t2 = rem.pop(best_i)
                q1, q2 = t2
                
                matches.append((t1, t2))
                rivals_count[p1].add(q1)
                rivals_count[p1].add(q2)
                rivals_count[p2].add(q1)
                rivals_count[p2].add(q2)
                rivals_count[q1].add(p1)
                rivals_count[q1].add(p2)
                rivals_count[q2].add(p1)
                rivals_count[q2].add(p2)
            
            if possible and all(len(rivals_count[p]) == N - 1 for p in players):
                return matches
        return None

    match_pairs = solve()
    
    if not match_pairs:
        rem = list(all_pairs)
        match_pairs = []
        while len(rem) >= 2:
            t1 = rem.pop(0)
            p1, p2 = t1
            paired = False
            for i, t2 in enumerate(rem):
                q1, q2 = t2
                if q1 != p1 and q1 != p2 and q2 != p1 and q2 != p2:
                    match_pairs.append((t1, t2))
                    rem.pop(i)
                    paired = True
                    break
            if not paired:
                pass

    rounds_list = []
    curr_round = []
    used_in_round = set()
    
    for (p1, p2), (q1, q2) in match_pairs:
        m_players = {p1, p2, q1, q2}
        if len(m_players.intersection(used_in_round)) > 0 or len(curr_round) >= courts_count:
            if curr_round:
                rounds_list.append(curr_round)
            curr_round = [((p1, p2), (q1, q2))]
            used_in_round = set(m_players)
        else:
            curr_round.append(((p1, p2), (q1, q2)))
            used_in_round.update(m_players)
            
    if curr_round:
        rounds_list.append(curr_round)
        
    matches = []
    match_id = start_match_id
    for r_idx, r_matches in enumerate(rounds_list, 1):
        for court_idx, ((p1, p2), (q1, q2)) in enumerate(r_matches, 1):
            matches.append({
                "id": f"m_{match_id}",
                "group": group_name,
                "round": r_idx,
                "court": ((court_idx - 1) % courts_count) + 1,
                "p1": p1,
                "p2": p2,
                "p3": q1,
                "p4": q2,
                "scoreA": "",
                "scoreB": "",
                "status": "pending",
                "confirmed": False
            })
            match_id += 1
            
    return matches

# ==========================================
# PESTAÑA 1: RANKING POR GRUPOS
# ==========================================
if selected_tab == "📊 Ranking por Grupos":
    st.subheader("Tabla de Posiciones por Grupo")
    st.caption("Puntaje basado en games ganados de forma individual.")
    
    active_groups = sorted(list(set([p["group"] for p in st.session_state.players])))
    if not active_groups:
        st.info("No hay jugadoras inscritas ni grupos generados.")
    else:
        if st.session_state.active_standings_group not in active_groups:
            st.session_state.active_standings_group = active_groups[0]
            
        cols_g = st.columns(len(active_groups))
        for idx, g in enumerate(active_groups):
            with cols_g[idx]:
                if st.button(f"Grupo {g}", use_container_width=True, type="primary" if st.session_state.active_standings_group == g else "secondary"):
                    st.session_state.active_standings_group = g
                    st.rerun()
                    
        g_target = st.session_state.active_standings_group
        group_players = [p for p in st.session_state.players if p["group"] == g_target]
        
        stats = {p["name"]: {"name": p["name"], "total_matches": 0, "pj": 0, "pg": 0, "pp": 0, "gamesWon": 0, "gamesLost": 0, "points": 0} for p in group_players}
        
        group_matches = [m for m in st.session_state.matches if m["group"] == g_target]
        
        for m in group_matches:
            for pName in [m["p1"], m["p2"], m["p3"], m["p4"]]:
                if pName in stats:
                    stats[pName]["total_matches"] += 1

        for m in group_matches:
            if m["status"] == "finished" and m["confirmed"]:
                sA = m["scoreA"]
                sB = m["scoreB"]
                if not pd.isna(sA) and not pd.isna(sB):
                    a_win = sA > sB
                    b_win = sB > sA
                    
                    for pName in [m["p1"], m["p2"]]:
                        if pName in stats:
                            stats[pName]["pj"] += 1
                            if a_win: stats[pName]["pg"] += 1
                            elif b_win: stats[pName]["pp"] += 1
                            stats[pName]["gamesWon"] += sA
                            stats[pName]["gamesLost"] += sB
                            stats[pName]["points"] += sA
                            
                    for pName in [m["p3"], m["p4"]]:
                        if pName in stats:
                            stats[pName]["pj"] += 1
                            if b_win: stats[pName]["pg"] += 1
                            elif a_win: stats[pName]["pp"] += 1
                            stats[pName]["gamesWon"] += sB
                            stats[pName]["gamesLost"] += sA
                            stats[pName]["points"] += sB
                            
        sorted_stats = sorted(list(stats.values()), key=lambda x: (x["points"], x["gamesWon"] - x["gamesLost"], x["gamesWon"]), reverse=True)
        
        if not sorted_stats:
            st.info(f"Sin jugadoras en el Grupo {g_target}")
        else:
            df_standings = pd.DataFrame(sorted_stats)
            df_standings.insert(0, "Pos", [f"{i+1}º" for i in range(len(df_standings))])
            df_standings["Dif"] = df_standings["gamesWon"] - df_standings["gamesLost"]
            df_standings = df_standings[["Pos", "name", "total_matches", "pj", "pg", "pp", "gamesWon", "gamesLost", "Dif", "points"]]
            df_standings.columns = ["Pos", "Jugadora", "P. Tot.", "PJ", "PG", "PP", "Games +", "Games -", "Dif", "Puntos (Games Totales)"]
            st.dataframe(df_standings, use_container_width=True, hide_index=True)

# ==========================================
# PESTAÑA 2: JUGADORAS Y VERIFICACIÓN
# ==========================================
elif selected_tab == "🔍 Jugadoras y Verificación":
    st.subheader("Resumen y Verificación de Jugadora")
    st.caption("Verifica si la jugadora ya se enfrentó a todas y si compartió cancha con todas las compañeras posibles.")
    
    if not st.session_state.players:
        st.info("No hay jugadoras cargadas.")
    else:
        player_names = [p["name"] for p in st.session_state.players]
        selected_player_name = st.selectbox("Seleccione Jugadora", player_names)
        
        player_obj = next((p for p in st.session_state.players if p["name"] == selected_player_name), None)
        if player_obj:
            g_key = player_obj["group"]
            group_players = [p for p in st.session_state.players if p["group"] == g_key]
            p_matches = [m for m in st.session_state.matches if m["group"] == g_key and (m["p1"] == selected_player_name or m["p2"] == selected_player_name or m["p3"] == selected_player_name or m["p4"] == selected_player_name)]
            
            compis_unicas = set()
            rivales_conteo = {}
            
            for m in p_matches:
                is_team_a = (m["p1"] == selected_player_name or m["p2"] == selected_player_name)
                partner = (m["p2"] if m["p1"] == selected_player_name else m["p1"]) if is_team_a else (m["p4"] if m["p3"] == selected_player_name else m["p3"])
                if partner: compis_unicas.add(partner)
                
                opponents = [m["p3"], m["p4"]] if is_team_a else [m["p1"], m["p2"]]
                for opp in opponents:
                    rivales_conteo[opp] = rivales_conteo.get(opp, 0) + 1
                    
            posibles_compis = [p["name"] for p in group_players if p["name"] != selected_player_name]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📊 Estado de Compañeras")
                st.write(f"Has jugado con **{len(compis_unicas)}** de **{len(posibles_compis)}** compañeras posibles en tu grupo.")
                for c in posibles_compis:
                    is_c = c in compis_unicas
                    st.markdown(f"- {c}: **{'✔️ Compañera' if is_c else 'Pendiente'}**")
                    
            with col2:
                st.markdown("### ⚔️ Estado de Rivales")
                st.write(f"Te has enfrentado a **{len(rivales_conteo)}** de **{len(posibles_compis)}** rivales posibles.")
                for r in posibles_compis:
                    count = rivales_conteo.get(r, 0)
                    st.markdown(f"- {r}: **{f'Enfrentamientos: {count}' if count > 0 else 'Sin cruce'}**")
                    
            st.divider()
            st.markdown("### 📅 Historial Detallado de Partidos")
            if not p_matches:
                st.info("Sin partidos registrados en este grupo.")
            else:
                for m in p_matches:
                    is_team_a = (m["p1"] == selected_player_name or m["p2"] == selected_player_name)
                    partner = (m["p2"] if m["p1"] == selected_player_name else m["p1"]) if is_team_a else (m["p4"] if m["p3"] == selected_player_name else m["p3"])
                    rivals = f"{m['p3']} / {m['p4']}" if is_team_a else f"{m['p1']} / {m['p2']}"
                    res_str = f"{m['scoreA']} - {m['scoreB']}" if m["scoreA"] != "" and m["scoreB"] != "" else "Pendiente"
                    st.info(f"**Ronda {m['round']} - Cancha {m['court']}** | Compañera: **{partner}** | Rivales: {rivals} | Resultado: **{res_str}**")

# ==========================================
# PESTAÑA 3: FIXTURE Y RESULTADOS
# ==========================================
elif selected_tab == "📅 Fixture y Resultados":
    st.subheader("Fixture y Resultados por Grupos")
    st.caption("Visualiza todos los grupos en columnas. Las tarjetas de partidos programados tienen fondo destacado.")
    
    if not st.session_state.matches:
        st.warning("Aún no hay partidos generados. Ve a la pestaña de Configuración para generar el fixture.")
    else:
        total_g = st.session_state.num_groups
        groups = [get_group_letter(i) for i in range(total_g)]
        
        cols = st.columns(len(groups))
        for idx, gKey in enumerate(groups):
            with cols[idx]:
                g_matches = [m for m in st.session_state.matches if m["group"] == gKey]
                total_gm = len(g_matches)
                finished_gm = len([m for m in g_matches if m["status"] == "finished"])
                pending_rounds = [m["round"] for m in g_matches if m["status"] != "finished"]
                active_round = min(pending_rounds) if pending_rounds else None
                in_play_gm = len([m for m in g_matches if m["status"] != "finished" and m["round"] == active_round]) if active_round else 0
                remaining_gm = total_gm - finished_gm - in_play_gm

                st.markdown(f"### Grupo {gKey}")
                st.caption(f"📊 **Total:** {total_gm} | ✅ **Jugados:** {finished_gm} | 🟢 **En juego:** {in_play_gm} | ⏳ **Faltantes:** {remaining_gm}")

                if not g_matches:
                    st.caption("Sin partidos.")
                
                for m in g_matches:
                    if m["status"] == "finished":
                        status_label = "Finalizado"
                        badge = "🔴"
                        bg_color = "#ffffff"
                        border_color = "#cbd5e1"
                    elif m["round"] == active_round:
                        status_label = "En juego"
                        badge = "🟢"
                        bg_color = "#ffffff"
                        border_color = "#22c55e"
                    else:
                        status_label = "Programado"
                        badge = "🟡"
                        bg_color = "#fef9c3"
                        border_color = "#eab308"
                        
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <style>
                            div[data-testid="stVerticalBlock"]:has(.card-marker-{m['id']}) {{
                                background-color: {bg_color} !important;
                                border: 2px solid {border_color} !important;
                                padding: 6px 10px !important;
                                border-radius: 8px !important;
                            }}
                            </style>
                            <div class="card-marker-{m['id']}" style="display:none;"></div>
                            <div style="font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 2px; display: flex; justify-content: space-between; align-items: center;">
                                <span>Ronda {m['round']} - Cancha {m['court']}</span>
                                <span>{badge} {status_label}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        cA1, cA2 = st.columns([3, 1])
                        with cA1:
                            st.markdown(f"<div style='font-size: 12px; font-weight: 600; padding-top: 6px;'>{m['p1']} / {m['p2']}</div>", unsafe_allow_html=True)
                        with cA2:
                            sA = st.number_input("Gs A", value=int(m["scoreA"]) if m["scoreA"] != "" else 0, key=f"sA_{m['id']}", disabled=not st.session_state.admin_auth or m["confirmed"], label_visibility="collapsed")
                        
                        cB1, cB2 = st.columns([3, 1])
                        with cB1:
                            st.markdown(f"<div style='font-size: 12px; font-weight: 600; padding-top: 6px;'>{m['p3']} / {m['p4']}</div>", unsafe_allow_html=True)
                        with cB2:
                            sB = st.number_input("Gs B", value=int(m["scoreB"]) if m["scoreB"] != "" else 0, key=f"sB_{m['id']}", disabled=not st.session_state.admin_auth or m["confirmed"], label_visibility="collapsed")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("✏️ Modif.", key=f"mod_{m['id']}", use_container_width=True):
                                if st.session_state.admin_auth:
                                    m["confirmed"] = False
                                    st.rerun()
                                else:
                                    st.error("PIN")
                        with col_btn2:
                            if st.button("💾 Guardar", key=f"save_{m['id']}", disabled=not st.session_state.admin_auth or m["confirmed"], use_container_width=True):
                                m["scoreA"] = sA
                                m["scoreB"] = sB
                                m["status"] = "finished"
                                m["confirmed"] = True
                                st.success("OK")
                                st.rerun()

# ==========================================
# PESTAÑA 4: CONFIGURACIÓN Y SORTEO
# ==========================================
elif selected_tab == "⚙️ Configuración y Sorteo":
    st.subheader("1. Sorteo y Carga de Jugadoras")
    st.caption("Define cuántos grupos quieres y al agregar nombres el sistema los organizará de forma equilibrada.")
    
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        new_num_groups = st.number_input("Cantidad de Grupos", min_value=1, max_value=10, value=st.session_state.num_groups)
        if new_num_groups != st.session_state.num_groups:
            st.session_state.num_groups = new_num_groups
            st.rerun()
            
        new_courts = st.number_input("Cantidad de Canchas Disponibles", min_value=1, max_value=12, value=st.session_state.courts_count)
        st.session_state.courts_count = new_courts
        
    with col_conf2:
        st.write(f"**Total jugadoras inscritas:** {len(st.session_state.players)}")
        
    st.divider()
    
    col_add1, col_add2 = st.columns(2)
    with col_add1:
        with st.form("single_player_form", clear_on_submit=True):
            p_name = st.text_input("Nombre y Apellido")
            submitted_p = st.form_submit_button("🎲 Agregar Jugadora")
            if submitted_p and p_name.strip():
                assigned_group = assign_random_group()
                st.session_state.players.append({
                    "id": f"p_{len(st.session_state.players)}_{hash(p_name)}",
                    "name": p_name.strip(),
                    "group": assigned_group
                })
                st.success(f"¡Agregada {p_name} al Grupo {assigned_group}!")
                st.rerun()
                
    with col_add2:
        with st.form("bulk_player_form", clear_on_submit=True):
            bulk_text = st.text_area("Carga Masiva (una por línea)", placeholder="Jugadora 1\nJugadora 2")
            submitted_bulk = st.form_submit_button("Cargar Múltiples")
            if submitted_bulk and bulk_text.strip():
                names = [n.strip() for n in bulk_text.split("\n") if n.strip()]
                for name in names:
                    assigned_group = assign_random_group()
                    st.session_state.players.append({
                        "id": f"p_{len(st.session_state.players)}_{hash(name)}",
                        "name": name,
                        "group": assigned_group
                    })
                st.success(f"¡{len(names)} jugadoras cargadas con éxito!")
                st.rerun()
                
    st.divider()
    st.subheader("Listado de Jugadoras por Grupo")
    if not st.session_state.players:
        st.info("Sin jugadoras inscritas.")
    else:
        total_g = st.session_state.num_groups
        groups_map = {get_group_letter(i): [] for i in range(total_g)}
        for p in st.session_state.players:
            g = p.get("group", "A")
            if g in groups_map:
                groups_map[g].append(p)
                
        cols_disp = st.columns(min(len(groups_map), 4) if len(groups_map) > 0 else 1)
        for idx, (gKey, p_list) in enumerate(groups_map.items()):
            with cols_disp[idx % len(cols_disp)]:
                with st.container(border=True):
                    st.markdown(f"**Grupo {gKey}** ({len(p_list)})")
                    for p in p_list:
                        col_n, col_d = st.columns([4, 1])
                        with col_n:
                            st.text(p["name"])
                        with col_d:
                            if st.button("✕", key=f"del_{p['id']}"):
                                if st.session_state.admin_auth:
                                    st.session_state.players = [x for x in st.session_state.players if x["id"] != p["id"]]
                                    st.rerun()
                                else:
                                    st.error("Requiere PIN")
                                    
    st.divider()
    st.subheader("2. Generación de Fixture y Parámetros")
    
    col_gen1, col_gen2 = st.columns(2)
    with col_gen1:
        if st.button("🎲 Generar Fixture 100% Cruzado", type="primary", use_container_width=True):
            if len(st.session_state.players) < 4:
                st.error("Se necesitan al menos 4 jugadoras en total.")
            else:
                groups = {}
                for p in st.session_state.players:
                    groups.setdefault(p["group"], []).append(p["name"])
                    
                new_matches = []
                match_id = 1
                generated_count = 0
                
                for gKey, gPlayers in groups.items():
                    if len(gPlayers) < 4:
                        continue
                    generated_count += 1
                    group_generated = generate_americano_schedule(gPlayers, gKey, match_id, st.session_state.courts_count)
                    new_matches.extend(group_generated)
                    match_id += len(group_generated)
                    
                if generated_count == 0:
                    st.error("Ningún grupo cuenta con el mínimo de 4 jugadoras requeridas.")
                else:
                    st.session_state.matches = new_matches
                    st.success("¡Fixture generado con 100% de cruces de compañeras y rivales garantizados!")
                    st.rerun()
                    
    with col_gen2:
        if st.button("⚠️ Reiniciar Torneo Completo", use_container_width=True):
            if st.session_state.admin_auth:
                st.session_state.players = []
                st.session_state.matches = []
                st.success("Torneo reiniciado.")
                st.rerun()
            else:
                st.error("Requiere PIN de Administrador.")
