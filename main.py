import flet as ft
import threading
import time
import os
import requests  

def main(page: ft.Page):
    page.title = "StarRun Premium"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 12
    
    # Contentor principal síncrono e ultraveloz
    palco = ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    page.add(palco)

    # ==========================================
    # SISTEMA DE ÁUDIO RECONFIGURADO CONTRA CRASH
    # ==========================================
    snd_bg = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/ambient_space_drive.ogg", autoplay=False, volume=0.2, release_mode="loop")
    snd_jump = ft.Audio(src="https://actions.google.com/sounds/v1/cartoon/slide_whistle_up.ogg", autoplay=False, volume=0.4)
    snd_point = ft.Audio(src="https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg", autoplay=False, volume=0.4)
    snd_over = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/space_emergency.ogg", autoplay=False, volume=0.5)
    
    page.overlay.extend([snd_bg, snd_jump, snd_point, snd_over])

    # --- ESTADO DE SESSÃO DO JOGADOR ---
    state = {
        "saldo": 0.00,
        "pontos": 0,
        "vidas": 3,
        "anuncios_assistidos": 0,
        "skin_atual": "⭐",
        "cenario_atual": "Espaço Oblívio",
        "skins_desbloqueadas": ["⭐"],
        "cenarios_comprados": ["Espaço Oblívio"],
        "running": False, 
        "is_jumping": False, 
        "velocity_y": 0.0,
        "star_bottom": 0, 
        "obstacle_left": 310, 
        "obstacle_speed": 12.0,
        "score_session": 0, 
        "fase_atual": 1,
        "tela_cheia": False,
        # Controle do Sistema de Temas Premium
        "temas_desbloqueados": ["Padrão Cyber"],
        "tema_custom_atual": "Padrão Cyber"
    }

    # Paleta de Cores dos Cenários da Loja
    cores_cenarios = {"Espaço Oblívio": "#111111", "Deserto Escaldante": "#3a2212", "Cyberpunk Neon": "#1a0033"}

    # Configuração Visual dos Temas Extras do Site
    estilos_temas = {
        "Padrão Cyber": {"bg": "#111111", "card": "#1e1e1e", "texto": "amber400"},
        "Vulcão Ultravioleta": {"bg": "#230026", "card": "#3d0042", "texto": "pink300"},
        "Oceano Profundo": {"bg": "#021124", "card": "#052247", "texto": "cyan400"},
        "Floresta Esmeralda": {"bg": "#051c0e", "card": "#0c3b1e", "texto": "green400"}
    }

    # --- CARREGAMENTO SEGURO E PROTEGIDO CONTRA TIMEOUT ---
    def carregar_sessao_salva():
        try:
            s = page.client_storage.get("starrun_saldo")
            if s is not None: state["saldo"] = float(s)
            p = page.client_storage.get("starrun_pontos")
            if p is not None: state["pontos"] = int(p)
            a = page.client_storage.get("starrun_ads")
            if a is not None: state["anuncios_assistidos"] = int(a)
            sk = page.client_storage.get("starrun_skin")
            if sk is not None: state["skin_atual"] = sk
            ce = page.client_storage.get("starrun_cenario")
            if ce is not None: state["cenario_atual"] = ce
            
            t_desb = page.client_storage.get("starrun_temas_desb")
            if t_desb: state["temas_desbloqueados"] = t_desb.split(",")
            t_at = page.client_storage.get("starrun_tema_at")
            if t_at: state["tema_custom_atual"] = t_at
            
            skins_salvas = page.client_storage.get("starrun_inv_skins")
            if skins_salvas: state["skins_desbloqueadas"] = skins_salvas.split(",")
            cenarios_salvos = page.client_storage.get("starrun_inv_cenarios")
            if cenarios_salvos: state["cenarios_comprados"] = cenarios_salvos.split(",")
        except Exception:
            pass

    def salvar_progresso_local():
        try:
            page.client_storage.set("starrun_saldo", str(state["saldo"]))
            page.client_storage.set("starrun_pontos", str(state["pontos"]))
            page.client_storage.set("starrun_ads", str(state["anuncios_assistidos"]))
            page.client_storage.set("starrun_skin", state["skin_atual"])
            page.client_storage.set("starrun_cenario", state["cenario_atual"])
            page.client_storage.set("starrun_tema_at", state["tema_custom_atual"])
            page.client_storage.set("starrun_temas_desb", ",".join(state["temas_desbloqueados"]))
            page.client_storage.set("starrun_inv_skins", ",".join(state["skins_desbloqueadas"]))
            page.client_storage.set("starrun_inv_cenarios", ",".join(state["cenarios_comprados"]))
        except Exception:
            pass

    def atualizar_financeiro(novos_pontos):
        state["pontos"] += novos_pontos
        state["saldo"] = state["pontos"] * 0.001
        salvar_progresso_local()

    # ==========================================
    # CABEÇALHO PERSISTENTE COM BOTÃO DE CONFIGURAÇÕES
    # ==========================================
    def obter_cabecalho():
        tema_at = estilos_temas.get(state["tema_custom_atual"], estilos_temas["Padrão Cyber"])
        
        def abrir_configuracoes(e):
            def alterar_modo_claro_escuro(e):
                page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
                page.update()

            def processar_desbloqueio_tema(nome_tema):
                def acao(e):
                    if nome_tema in state["temas_desbloqueados"]:
                        state["tema_custom_atual"] = nome_tema
                        salvar_progresso_local()
                        dialogo_config.open = False
                        mostrar_tela_principal()
                    else:
                        # Assiste anúncio para desbloquear o tema selecionado
                        page.launch_url("https://omg10.com/4/11105173")
                        state["anuncios_assistidos"] += 1
                        state["temas_desbloqueados"].append(nome_tema)
                        state["tema_custom_atual"] = nome_tema
                        salvar_progresso_local()
                        dialogo_config.open = False
                        mostrar_tela_principal()
                return acao

            opcoes_temas = ft.Column(spacing=8)
            for t_nome in estilos_temas.keys():
                liberado = t_nome in state["temas_desbloqueados"]
                txt_btn = f"Equipar {t_nome}" if liberado else f"🔓 Desbloquear {t_nome} (1 Ad)"
                cor_btn = "blue700" if liberado else "purple700"
                opcoes_temas.controls.append(
                    ft.ElevatedButton(txt_btn, bgcolor=cor_btn, color="white", width=280, on_click=processar_desbloqueio_tema(t_nome))
                )

            dialogo_config.content = ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes Visuais do App", weight="bold", size=16),
                    ft.Divider(),
                    ft.ElevatedButton("Alternar Modo Claro/Escuro ☀️🌙", bgcolor="grey800", color="white", width=280, on_click=alterar_mode_claro_escuro),
                    ft.Container(height=10),
                    ft.Text("Temas Premium Disponíveis:", size=13, color="white60"),
                    opcoes_temas
                ], main_axis_size=ft.MainAxisSize.MIN, horizontal_alignment="center"),
                width=300, padding=5
            )
            dialogo_config.open = True
            page.update()

        def fechar_dialogo(e):
            dialogo_config.open = False
            page.update()

        dialogo_config = ft.AlertDialog(
            actions=[ft.TextButton("Fechar", on_click=fechar_dialogo)],
            actions_alignment="end"
        )
        page.overlay.append(dialogo_config)

        return ft.Container(
            content=ft.Row([
                ft.Text("StarRun Premium", size=22, weight="bold", color=tema_at["texto"]),
                ft.IconButton(ft.icons.SETTINGS, icon_color=tema_at["texto"], tooltip="Configurações", on_click=abrir_configuracoes)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            width=340, padding=ft.padding.only(bottom=10)
        )

    # ==========================================
    # TELA 1: MENU PRINCIPAL
    # ==========================================
    def mostrar_tela_principal(e=None):
        state["running"] = False 
        page.on_keyboard_event = None 
        palco.controls.clear() 
        
        try: snd_bg.play()
        except Exception: pass

        tema_at = estilos_temas.get(state["tema_custom_atual"], estilos_temas["Padrão Cyber"])
        page.bgcolor = tema_at["bg"]

        palco.controls.extend([
            obter_cabecalho(),
            ft.Card(
                color=tema_at["card"],
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Seu Saldo Disponível", size=13, color="white60"),
                        ft.Text(f"R$ {state['saldo']:.2f}", size=34, weight="bold", color="green400"),
                        ft.Text(f"Pontos Totais: {state['pontos']} pts", size=13, color="white40"),
                    ], horizontal_alignment="center"),
                    padding=15, width=330
                )
            ),
            ft.Text(f"Vidas: {state['vidas']} ❤️ | Skin: {state['skin_atual']} | Mapa: {state['cenario_atual']}", size=12, color="white54", text_align="center"),
            ft.Container(height=10),
            ft.ElevatedButton("Jogar Corrida Estelar 🕹️", bgcolor="green700", color="white", width=280, height=45, on_click=mostrar_tela_jogo),
            ft.ElevatedButton("Loja de Cenários 🛒", bgcolor="blue700", color="white", width=280, height=45, on_click=mostrar_loja_cenarios),
            ft.ElevatedButton("Desbloquear Skins 📺", bgcolor="purple700", color="white", width=280, height=45, on_click=mostrar_loja_skins),
            ft.ElevatedButton("Sacar via Pix 💰", bgcolor="teal700", color="white", width=280, height=45, on_click=mostrar_tela_pix),
        ])
        page.update()

    # ==========================================
    # TELA 2: MOTOR GRÁFICO DO JOGO (THREAD ISOLADA)
    # ==========================================
    def mostrar_tela_jogo(e=None):
        palco.controls.clear()
        state["star_bottom"] = 0
        state["score_session"] = 0
        state["fase_atual"] = 1

        largura_arena = 440 if state["tela_cheia"] else 340
        altura_arena = 180 if state["tela_cheia"] else 130
        state["obstacle_left"] = largura_arena - 30

        star = ft.Container(content=ft.Text(state["skin_atual"], size=26), left=40, bottom=0, animate=ft.animation.Animation(80, "linear"))
        obstacle = ft.Container(content=ft.Text("🌵", size=24), left=state["obstacle_left"], bottom=0, animate=ft.animation.Animation(80, "linear"))
        chao = ft.Container(width=largura_arena, height=2, bgcolor="white54", bottom=0)
        
        game_stack = ft.Stack([chao, star, obstacle], width=largura_arena, height=altura_arena)
        
        def realizar_pulo(event_data):
            if not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 16.0
                try: snd_jump.play() 
                except Exception: pass

        conteudo_jogo = ft.Container(
            content=game_stack, width=largura_arena, height=altura_arena,
            bgcolor=cores_cenarios.get(state["cenario_atual"], "#111111"),
            border_radius=10, border=ft.Border.all(width=1, color="white24"),
            on_click=realizar_pulo
        )

        def d_teclado(k: ft.KeyboardEvent):
            if k.key in ["Space", "Arrow Up"] and not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 16.0
                try: snd_jump.play()
                except Exception: pass

        page.on_keyboard_event = d_teclado

        placar_vidas = ft.Text(f"Vidas: {state['vidas']} ❤️", size=14, weight="bold", color="green400")
        placar_pontos = ft.Text("Pontos: 0", size=14, weight="bold")
        placar_fase = ft.Text("Fase: 1", size=14, weight="bold", color="amber400")
        text_instrucao = ft.Text("Toque na arena para pular!", size=13, color="white40")

        # CÁLCULO DE FÍSICA E COLISÃO ISOLADO NUMA THREAD BANCADA PELO SISTEMA
        def game_loop():
            gravity = 1.8
            while state["running"]:
                limite_arena = 440 if state["tela_cheia"] else 340
                
                state["obstacle_left"] -= state["obstacle_speed"]
                if state["obstacle_left"] < -20:
                    state["obstacle_left"] = limite_arena - 30
                    state["score_session"] += 10
                    placar_pontos.value = f"Pontos: {state['score_session']}"
                    try: snd_point.play()
                    except Exception: pass
                    
                    nova_fase = (state["score_session"] // 100) + 1
                    if nova_fase != state["fase_atual"]:
                        state["fase_atual"] = nova_fase
                        placar_fase.value = f"Fase: {state['fase_atual']}"
                        state["obstacle_speed"] += 2.0
                        if state["fase_atual"] == 2 and "🚀" not in state["skins_desbloqueadas"]:
                            state["skins_desbloqueadas"].append("🚀")
                            salvar_progresso_local()
                
                if state["is_jumping"]:
                    state["star_bottom"] += int(state["velocity_y"])
                    state["velocity_y"] -= gravity
                    if state["star_bottom"] <= 0:
                        state["star_bottom"] = 0
                        state["is_jumping"] = False
                
                star.bottom = state["star_bottom"]
                obstacle.left = state["obstacle_left"]
                
                if (20 <= state["obstacle_left"] <= 65) and state["star_bottom"] <= 25:
                    state["running"] = False
                    try: snd_over.play()
                    except Exception: pass
                    break
                
                conteudo_jogo.update()
                placar_pontos.update()
                time.sleep(0.08)

            state["vidas"] -= 1
            atualizar_financeiro(state["score_session"])
            botao_iniciar.text = "Jogar Novamente 🔄"
            botao_iniciar.visible = True
            
            if state["vidas"] <= 0:
                botao_iniciar.visible = False
                container_anuncio.visible = True
                text_instrucao.value = "Sem energia! Assista ao anúncio para recarregar."
                text_instrucao.color = "amber400"
            else:
                text_instrucao.value = f"Fim de jogo! Restam {state['vidas']} energias."
                text_instrucao.color = "red400"
                
            placar_vidas.value = f"Vidas: {state['vidas']} ❤️"
            page.update()

        def disparar_inicio(e):
            if state["vidas"] <= 0: return
            state["running"] = True
            state["obstacle_speed"] = 12.0
            botao_iniciar.visible = False
            page.update()
            # Dispara a Thread nativa do sistema operacional (Não trava o site)
            threading.Thread(target=game_loop, daemon=True).start()

        def recarregar_vidas_anuncio(e):
            page.launch_url("https://omg10.com/4/11105173")
            state["vidas"] = 3
            container_anuncio.visible = False
            botao_iniciar.visible = True
            placar_vidas.value = f"Vidas: {state['vidas']} ❤️"
            state["anuncios_assistidos"] += 1
            salvar_progresso_local()
            mostrar_tela_jogo()

        def alternar_ajuste_tela(e):
            state["tela_cheia"] = not state["tela_cheia"]
            mostrar_tela_jogo()

        botao_iniciar = ft.ElevatedButton("Iniciar Corrida 🚀", bgcolor="green700", color="white", width=180, on_click=disparar_inicio)
        container_anuncio = ft.Column([
            ft.ElevatedButton("Assistir Vídeo Premiado 📺", icon="play_circle", bgcolor="amber700", color="black", on_click=recarregar_vidas_anuncio)
        ], alignment="center")

        container_anuncio.visible = True if state["vidas"] <= 0 else False
        if state["vidas"] <= 0: botao_iniciar.visible = False

        btn_modo_tela = ft.IconButton(
            icon=ft.icons.FULLSCREEN_EXIT if state["tela_cheia"] else ft.icons.FULLSCREEN,
            icon_color="amber400",
            on_click=alternar_ajuste_tela
        )

        palco.controls.extend([
            obter_cabecalho(),
            ft.Row([ft.Text("🕹️ Arena StarRun", size=16, weight="bold"), btn_modo_tela], alignment="space_between", width=largura_arena),
            ft.Row([placar_vidas, placar_fase, placar_pontos], alignment="space_around", width=largura_arena),
            ft.Container(height=5),
            conteudo_jogo,
            ft.Container(height=15, content=text_instrucao),
            ft.Row([botao_iniciar, container_anuncio], alignment="center"),
            ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)
        ])
        page.update()

    # ==========================================
    # TELA 3: LOJA DE CENÁRIOS
    # ==========================================
    def mostrar_loja_cenarios(e=None):
        palco.controls.clear()
        lista_loja = ft.Column(spacing=10, horizontal_alignment="center")
        ofertas = [
            {"nome": "Espaço Oblívio", "preco": 0, "desc": "Mapa espacial clássico."},
            {"nome": "Deserto Escaldante", "preco": 500, "desc": "Terreno arenoso desafiador."},
            {"nome": "Cyberpunk Neon", "preco": 1500, "desc": "Estética neon futurista."}
        ]
        
        for item in ofertas:
            comprado = item["nome"] in state["cenarios_comprados"]
            ativo = state["cenario_atual"] == item["nome"]
            
            def criar_evento_compra(nome=item["nome"], preco=item["preco"]):
                def processar(e):
                    if nome in state["cenarios_comprados"]:
                        state["cenario_atual"] = nome
                    elif state["pontos"] >= preco:
                        state["pontos"] -= preco
                        state["cenarios_comprados"].append(nome)
                        state["cenario_atual"] = nome
                        salvar_progresso_local()
                    mostrar_loja_cenarios()
                return processar

            if ativo: btn = ft.ElevatedButton("Equipado ✅", disabled=True, width=110)
            elif comprado: btn = ft.ElevatedButton("Equipar", bgcolor="blue700", color="white", width=110, on_click=criar_evento_compra(item["nome"]))
            else: btn = ft.ElevatedButton(f"{item['preco']} Pts", bgcolor="amber700", color="black", width=110, on_click=criar_evento_compra(item["nome"], item["preco"]))

            lista_loja.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(item["nome"], weight="bold", size=14), ft.Text(item["desc"], size=11, color="white54")], expand=True), btn]), padding=8, border=ft.Border.all(1, "white24"), border_radius=8, width=340))

        palco.controls.extend([obter_cabecalho(), ft.Text("Loja de Cenários 🛒", size=24, weight="bold"), ft.Text(f"Seu Saldo: {state['pontos']} Pontos", color="amber400"), ft.Container(height=5), lista_loja, ft.Container(height=10), ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)])
        page.update()

    # ==========================================
    # TELA 4: LOJA DE SKINS
    # ==========================================
    def mostrar_loja_skins(e=None):
        palco.controls.clear()
        lista_skins = ft.Column(spacing=10, horizontal_alignment="center")
        catalogo = [
            {"skin": "⭐", "tipo": "Livre", "req": 0, "info": "A estrela clássica."},
            {"skin": "☄️", "tipo": "Anúncios", "req": 2, "info": "Meteoro (Assista 2 Ads)."},
            {"skin": "🛸", "tipo": "Anúncios", "req": 5, "info": "OVNI Alienígena (Assista 5 Ads)."},
            {"skin": "🚀", "tipo": "Fase", "req": 2, "info": "Desbloqueado ao chegar à Fase 2."}
        ]

        for item in catalogo:
            comprado = item["skin"] in state["skins_desbloqueadas"]
            ativo = state["skin_atual"] == item["skin"]
            if not comprado and item["tipo"] == "Anúncios" and state["anuncios_assistidos"] >= item["req"]:
                state["skins_desbloqueadas"].append(item["skin"])
                comprado = True
                salvar_progresso_local()

            def criar_evento_skin(skin=item["skin"]):
                def processar(e):
                    state["skin_atual"] = skin
                    salvar_progresso_local()
                    mostrar_loja_skins()
                return processar

            def assistir_ad_skin(e):
                page.launch_url("https://omg10.com/4/11105173")
                state["anuncios_assistidos"] += 1
                salvar_progresso_local()
                mostrar_loja_skins()

            if ativo: btn = ft.ElevatedButton("Em uso ✨", disabled=True, width=120)
            elif comprado: btn = ft.ElevatedButton("Selecionar", bgcolor="blue700", color="white", width=120, on_click=criar_evento_skin(item["skin"]))
            elif item["tipo"] == "Fase": btn = ft.Text(f"Bloqueado (Fase {item['req']})", color="red400", size=11, weight="bold")
            else: btn = ft.ElevatedButton(f"Ver Ad ({state['anuncios_assistidos']}/{item['req']})", bgcolor="purple700", color="white", width=120, on_click=assistir_ad_skin)

            lista_skins.controls.append(ft.Container(content=ft.Row([ft.Text(item["skin"], size=26), ft.Column([ft.Text(item["info"], size=11, color="white70")], expand=True), btn]), padding=8, border=ft.Border.all(1, "white12"), border_radius=8, width=340))

        palco.controls.extend([obter_cabecalho(), ft.Text("Skins Premiadas 📺", size=24, weight="bold"), ft.Text(f"Histórico: {state['anuncios_assistidos']} anúncios assistidos", color="purple300"), ft.Container(height=5), lista_skins, ft.Container(height=10), ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)])
        page.update()

    # ==========================================
    # TELA 5: PAINEL PIX REAL ONLINE
    # ==========================================
    def mostrar_tela_pix(e=None):
        palco.controls.clear()
        tipo_chave = ft.Dropdown(label="Tipo de Chave", width=320, options=[ft.dropdown.Option("CPF"), ft.dropdown.Option("E-mail"), ft.dropdown.Option("Telefone")])
        campo_chave = ft.TextField(label="Insira sua Chave Pix", width=320)
        campo_valor = ft.TextField(label="Valor do Resgate (R$)", width=320, value=f"{state['saldo']:.2f}")

        def ejecutar_saque_real(e):
            try:
                v = float(campo_valor.value.replace(",", "."))
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Valor digitado inválido!"), bgcolor="red700")
                page.snack_bar.open = True
                page.update()
                return

            if not tipo_chave.value or not campo_chave.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os dados Pix!"), bgcolor="red700")
            elif v > state["saldo"]:
                page.snack_bar = ft.SnackBar(ft.Text("Saldo em conta insuficiente!"), bgcolor="red700")
            elif v < 10.00:
                page.snack_bar = ft.SnackBar(ft.Text("O saque mínimo obrigatório é R$ 10,00!"), bgcolor="amber800")
            else:
                API_TOKEN = os.getenv("GATEWAY_PIX_TOKEN", "DESATIVADO")
                
                if API_TOKEN == "DESATIVADO":
                    page.snack_bar = ft.SnackBar(ft.Text("Sandbox ativo: Chave válida, mas vincule a API no painel Render!"), bgcolor="amber900")
                else:
                    payload = {"key": campo_chave.value, "type": tipo_chave.value, "amount": v}
                    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
                    
                    try:
                        res = requests.post("https://api.asaas.com/v3/transfers", json=payload, headers=headers, timeout=10)
                        if res.status_code in [200, 201]:
                            page.snack_bar = ft.SnackBar(ft.Text("Transferência Pix enviada com sucesso!"), bgcolor="green700")
                        else:
                            page.snack_bar = ft.SnackBar(ft.Text("Gateway recusou a transação. Verifique os dados."), bgcolor="red700")
                    except Exception:
                        page.snack_bar = ft.SnackBar(ft.Text("Falha na comunicação com o servidor bancário."), bgcolor="red700")

                state["saldo"] -= v
                state["pontos"] = int(state["saldo"] / 0.001)
                salvar_progresso_local()
                mostrar_tela_principal()
                
            page.snack_bar.open = True
            page.update()

        palco.controls.extend([
            obter_cabecalho(),
            ft.Text("Solicitar Resgate Pix 💰", size=24, weight="bold"),
            ft.Container(content=ft.Column([
                ft.Text("📜 REGULAMENTO DE RETIRADA:", weight="bold", size=13, color="amber400"),
                ft.Text("• Limite de Saque Mínimo: R$ 10,00 por transação.", size=12),
                ft.Text("• Taxa Bancária: R$ 0,00 (Isento de tarifas).", size=12),
                ft.Text("• Processamento: Liquidado instantaneamente via API Gateway.", size=12),
            ], spacing=5), padding=12, bgcolor="#1a1a1a", border_radius=8, width=340),
            ft.Container(height=10),
            tipo_chave, campo_chave, campo_valor,
            ft.ElevatedButton("Confirmar Transação Pix 🚀", bgcolor="teal700", color="white", width=320, height=45, on_click=ejecutar_saque_real),
            ft.TextButton("Voltar ao Menu Principal", on_click=mostrar_tela_principal)
        ])
        page.update()

    # Inicialização segura do ecossistema síncrono
    carregar_sessao_salva()
    mostrar_tela_principal()

if __name__ == "__main__":
    porta = int(os.getenv("PORT", 8080))
    ft.app(target=main, port=porta, assets_dir="assets")