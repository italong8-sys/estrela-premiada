import flet as ft
import asyncio
import os
import requests  

async def main(page: ft.Page):
    page.title = "StarRun Premium"
    page.theme_mode = "dark"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.padding = 12
    
    # Contentor principal adaptável para qualquer ecrã (Telemóvel ou PC)
    palco = ft.Column(alignment="center", horizontal_alignment="center", spacing=10)
    page.controls.append(palco)
    await page.update_async() 

    # ==========================================
    # CONTROLADORES DE ÁUDIO COM PROTEÇÃO CONTRA CRASH
    # ==========================================
    snd_bg = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/ambient_space_drive.ogg", autoplay=False, volume=0.2, release_mode="loop")
    snd_jump = ft.Audio(src="https://actions.google.com/sounds/v1/cartoon/slide_whistle_up.ogg", autoplay=False, volume=0.4)
    snd_point = ft.Audio(src="https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg", autoplay=False, volume=0.4)
    snd_over = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/space_emergency.ogg", autoplay=False, volume=0.5)
    
    page.overlay.extend([snd_bg, snd_jump, snd_point, snd_over])

    # --- ESTADO DE SESSÃO DO UTILIZADOR ---
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
        "loop_lock": False # Impede que cliques duplos multipliquem o jogo
    }

    cores_cenarios = {"Espaço Oblívio": "#111111", "Deserto Escaldante": "#3a2212", "Cyberpunk Neon": "#1a0033"}

    # --- CARREGAMENTO SEGURO E ASSÍNCRONO DE DADOS ---
    async def carregar_sessao_salva():
        try:
            await asyncio.sleep(0.5)
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
            
            skins_salvas = page.client_storage.get("starrun_inv_skins")
            if skins_salvas: state["skins_desbloqueadas"] = skins_salvas.split(",")
            cenarios_salvos = page.client_storage.get("starrun_inv_cenarios")
            if cenarios_salvos: state["cenarios_comprados"] = cenarios_salvos.split(",")
            await mostrar_tela_principal()
        except Exception:
            await mostrar_tela_principal()

    async def salvar_progresso_local():
        try:
            page.client_storage.set("starrun_saldo", str(state["saldo"]))
            page.client_storage.set("starrun_pontos", str(state["pontos"]))
            page.client_storage.set("starrun_ads", str(state["anuncios_assistidos"]))
            page.client_storage.set("starrun_skin", state["skin_atual"])
            page.client_storage.set("starrun_cenario", state["cenario_atual"])
            page.client_storage.set("starrun_inv_skins", ",".join(state["skins_desbloqueadas"]))
            page.client_storage.set("starrun_inv_cenarios", ",".join(state["cenarios_comprados"]))
        except Exception:
            pass

    async def atualizar_financeiro(novos_pontos):
        state["pontos"] += novos_pontos
        state["saldo"] = state["pontos"] * 0.001
        await salvar_progresso_local()

    # ==========================================
    # TELA 1: MENU PRINCIPAL
    # ==========================================
    async def mostrar_tela_principal(e=None):
        state["running"] = False 
        page.on_keyboard_event = None 
        palco.controls.clear() 
        
        try:
            await snd_bg.play_async()
        except Exception:
            pass

        palco.controls.extend([
            ft.Text("✨ StarRun Premium ✨", size=28, weight="bold", color="amber400", text_align="center"),
            ft.Container(height=5),
            ft.Card(
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
            ft.ElevatedButton("Jogar Corrida Estelar 🕹️", bgcolor="green700", color="white", width=260, height=45, on_click=mostrar_tela_jogo),
            ft.ElevatedButton("Loja de Cenários 🛒", bgcolor="blue700", color="white", width=260, height=45, on_click=mostrar_loja_cenarios),
            ft.ElevatedButton("Desbloquear Skins 📺", bgcolor="purple700", color="white", width=260, height=45, on_click=mostrar_loja_skins),
            ft.ElevatedButton("Sacar via Pix 💰", bgcolor="teal700", color="white", width=260, height=45, on_click=mostrar_tela_pix),
        ])
        await page.update_async()

    # ==========================================
    # TELA 2: MOTOR GRÁFICO DO JOGO (PC & MOBILE)
    # ==========================================
    async def mostrar_tela_jogo(e=None):
        palco.controls.clear()
        state["star_bottom"] = 0
        state["score_session"] = 0
        state["fase_atual"] = 1

        # Controle de Ajuste de Tela Cheia Inteligente
        largura_arena = min(page.width - 20, 600) if state["tela_cheia"] else 340
        altura_arena = 180 if state["tela_cheia"] else 130
        state["obstacle_left"] = largura_arena - 30

        # Suavização de movimentos via Hardware do cliente (Evita lag de WebSocket)
        star = ft.Container(content=ft.Text(state["skin_atual"], size=26), left=40, bottom=0, animate=ft.animation.Animation(90, "linear"))
        obstacle = ft.Container(content=ft.Text("🌵", size=24), left=state["obstacle_left"], bottom=0, animate=ft.animation.Animation(90, "linear"))
        chao = ft.Container(width=largura_arena, height=2, bgcolor="white54", bottom=0)
        
        game_stack = ft.Stack([chao, star, obstacle], width=largura_arena, height=altura_arena)
        
        async def realizar_pulo(event_data):
            if not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 16.0
                try: await snd_jump.play_async() 
                except Exception: pass

        conteudo_jogo = ft.Container(
            content=game_stack, width=largura_arena, height=altura_arena,
            bgcolor=cores_cenarios.get(state["cenario_atual"], "#111111"),
            border_radius=10, border=ft.Border.all(width=1, color="white24"),
            on_click=realizar_pulo
        )

        async def d_teclado(k: ft.KeyboardEvent):
            if k.key in ["Space", "Arrow Up"] and not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 16.0
                try: await snd_jump.play_async()
                except Exception: pass

        page.on_keyboard_event = d_teclado

        placar_vidas = ft.Text(f"Vidas: {state['vidas']} ❤️", size=14, weight="bold", color="green400")
        placar_pontos = ft.Text("Pontos: 0", size=14, weight="bold")
        placar_fase = ft.Text("Fase: 1", size=14, weight="bold", color="amber400")
        text_instrucao = ft.Text("Toque na tela para saltar!", size=13, color="white40")

        # LOOP REDUZIDO PARA PROTEGER A CONEXÃO DE REDE DO SERVER
        async def game_loop():
            gravity = 1.8
            while state["running"]:
                limite_arena = min(page.width - 20, 600) if state["tela_cheia"] else 340
                
                state["obstacle_left"] -= state["obstacle_speed"]
                if state["obstacle_left"] < -20:
                    state["obstacle_left"] = limite_arena - 30
                    state["score_session"] += 10
                    placar_pontos.value = f"Pontos: {state['score_session']}"
                    try: await snd_point.play_async()
                    except Exception: pass
                    
                    # Passagem Dinâmica de Fases
                    nova_fase = (state["score_session"] // 100) + 1
                    if nova_fase != state["fase_atual"]:
                        state["fase_atual"] = nova_fase
                        placar_fase.value = f"Fase: {state['fase_atual']}"
                        state["obstacle_speed"] += 2.0
                        if state["fase_atual"] == 2 and "🚀" not in state["skins_desbloqueadas"]:
                            state["skins_desbloqueadas"].append("🚀")
                            await salvar_progresso_local()
                
                if state["is_jumping"]:
                    state["star_bottom"] += int(state["velocity_y"])
                    state["velocity_y"] -= gravity
                    if state["star_bottom"] <= 0:
                        state["star_bottom"] = 0
                        state["is_jumping"] = False
                
                star.bottom = state["star_bottom"]
                obstacle.left = state["obstacle_left"]
                
                # Checagem de colisão calibrada para a taxa estável de frames
                if (20 <= state["obstacle_left"] <= 65) and state["star_bottom"] <= 25:
                    state["running"] = False
                    try: await snd_over.play_async()
                    except Exception: pass
                    break
                
                await conteudo_jogo.update_async()
                await placar_pontos.update_async()
                await asyncio.sleep(0.1) # Intervalo perfeito (Evita saturação do WebSocket)

            state["vidas"] -= 1
            await atualizar_financeiro(state["score_session"])
            botao_iniciar.text = "Jogar Novamente 🔄"
            botao_iniciar.visible = True
            state["loop_lock"] = False
            
            if state["vidas"] <= 0:
                botao_iniciar.visible = False
                container_anuncio.visible = True
                text_instrucao.value = "Sem energia! Assista ao anúncio para recarregar."
                text_instrucao.color = "amber400"
            else:
                text_instrucao.value = f"Fim de jogo! Restam {state['vidas']} energias."
                text_instrucao.color = "red400"
                
            placar_vidas.value = f"Vidas: {state['vidas']} ❤️"
            await page.update_async()

        async def disparar_inicio(e):
            if state["vidas"] <= 0 or state["loop_lock"]: return
            state["running"] = True
            state["loop_lock"] = True
            state["obstacle_speed"] = 12.0
            botao_iniciar.visible = False
            await page.update_async()
            page.run_task(game_loop)

        async def recarregar_vidas_anuncio(e):
            await page.launch_url_async("https://omg10.com/4/11105173")
            state["vidas"] = 3
            container_anuncio.visible = False
            botao_iniciar.visible = True
            placar_vidas.value = f"Vidas: {state['vidas']} ❤️"
            state["anuncios_assistidos"] += 1
            await salvar_progresso_local()
            await mostrar_tela_jogo()

        async def alternar_ajuste_tela(e):
            state["tela_cheia"] = not state["tela_cheia"]
            await mostrar_tela_jogo()

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
            ft.Row([ft.Text("🕹️ Arena StarRun", size=16, weight="bold"), btn_modo_tela], alignment="space_between", width=largura_arena),
            ft.Row([placar_vidas, placar_fase, placar_pontos], alignment="space_around", width=largura_arena),
            ft.Container(height=5),
            conteudo_jogo,
            ft.Container(height=15, content=text_instrucao),
            ft.Row([botao_iniciar, container_anuncio], alignment="center"),
            ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)
        ])
        await page.update_async()

    # ==========================================
    # TELA 3: LOJA DE CENÁRIOS (SISTEMA DE PONTOS)
    # ==========================================
    async def mostrar_loja_cenarios(e=None):
        palco.controls.clear()
        lista_loja = ft.Column(spacing=10, horizontal_alignment="center")
        ofertas = [
            {"nome": "Espaço Oblívio", "preco": 0, "desc": "Mapa espacial clássico."},
            {"nome": "Deserto Escaldante", "preco": 500, "desc": "Terreno arenoso desafiador."},
            {"nome": "Cyberpunk Neon", "preco": 1500, "desc": "Estética neon de alta performance."}
        ]
        
        for item in ofertas:
            comprado = item["nome"] in state["cenarios_comprados"]
            ativo = state["cenario_atual"] == item["nome"]
            
            def criar_evento_compra(nome=item["nome"], preco=item["preco"]):
                async def processar(e):
                    if nome in state["cenarios_comprados"]:
                        state["cenario_atual"] = nome
                    elif state["pontos"] >= preco:
                        state["pontos"] -= preco
                        state["cenarios_comprados"].append(nome)
                        state["cenario_atual"] = nome
                        await salvar_progresso_local()
                    await mostrar_loja_cenarios()
                return processar

            if ativo: btn = ft.ElevatedButton("Equipado ✅", disabled=True, width=110)
            elif comprado: btn = ft.ElevatedButton("Equipar", bgcolor="blue700", color="white", width=110, on_click=criar_evento_compra(item["nome"]))
            else: btn = ft.ElevatedButton(f"{item['preco']} Pts", bgcolor="amber700", color="black", width=110, on_click=criar_evento_compra(item["nome"], item["preco"]))

            lista_loja.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(item["nome"], weight="bold", size=14), ft.Text(item["desc"], size=11, color="white54")], expand=True), btn]), padding=8, border=ft.Border.all(1, "white24"), border_radius=8, width=340))

        palco.controls.extend([ft.Text("Loja de Cenários 🛒", size=24, weight="bold"), ft.Text(f"Seu Saldo: {state['pontos']} Pontos", color="amber400"), ft.Container(height=5), lista_loja, ft.Container(height=10), ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)])
        await page.update_async()

    # ==========================================
    # TELA 4: DESBLOQUEIO DE SKINS (ANÚNCIOS / FASES)
    # ==========================================
    async def mostrar_loja_skins(e=None):
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
                await salvar_progresso_local()

            def criar_evento_skin(skin=item["skin"]):
                async def processar(e):
                    state["skin_atual"] = skin
                    await salvar_progresso_local()
                    await mostrar_loja_skins()
                return processar

            async def assistir_ad_skin(e):
                await page.launch_url_async("https://omg10.com/4/11105173")
                state["anuncios_assistidos"] += 1
                await salvar_progresso_local()
                await mostrar_loja_skins()

            if ativo: btn = ft.ElevatedButton("Em uso ✨", disabled=True, width=120)
            elif comprado: btn = ft.ElevatedButton("Selecionar", bgcolor="blue700", color="white", width=120, on_click=criar_evento_skin(item["skin"]))
            elif item["tipo"] == "Fase": btn = ft.Text(f"Bloqueado (Fase {item['req']})", color="red400", size=11, weight="bold")
            else: btn = ft.ElevatedButton(f"Ver Ad ({state['anuncios_assistidos']}/{item['req']})", bgcolor="purple700", color="white", width=120, on_click=assistir_ad_skin)

            lista_skins.controls.append(ft.Container(content=ft.Row([ft.Text(item["skin"], size=26), ft.Column([ft.Text(item["info"], size=11, color="white70")], expand=True), btn]), padding=8, border=ft.Border.all(1, "white12"), border_radius=8, width=340))

        palco.controls.extend([ft.Text("Skins Premiadas 📺", size=24, weight="bold"), ft.Text(f"Histórico: {state['anuncios_assistidos']} anúncios assistidos", color="purple300"), ft.Container(height=5), lista_skins, ft.Container(height=10), ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)])
        await page.update_async()

    # ==========================================
    # TELA 5: PAINEL PIX ONLINE VIA API GATEWAY
    # ==========================================
    async def mostrar_tela_pix(e=None):
        palco.controls.clear()
        tipo_chave = ft.Dropdown(label="Tipo de Chave", width=320, options=[ft.dropdown.Option("CPF"), ft.dropdown.Option("E-mail"), ft.dropdown.Option("Telefone")])
        campo_chave = ft.TextField(label="Insira sua Chave Pix", width=320)
        campo_valor = ft.TextField(label="Valor do Resgate (R$)", width=320, value=f"{state['saldo']:.2f}")

        # Executa a chamada HTTP de forma assíncrona isolada para não travar o ecrã do cliente
        async def executar_saque_real(e):
            try:
                v = float(campo_valor.value.replace(",", "."))
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Valor digitado inválido!"), bgcolor="red700")
                page.snack_bar.open = True
                await page.update_async()
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
                        # Roda a requisição síncrona numa thread paralela para manter os botões 100% ativos
                        res = await asyncio.to_thread(requests.post, "https://api.asaas.com/v3/transfers", json=payload, headers=headers, timeout=10)
                        if res.status_code in [200, 201]:
                            page.snack_bar = ft.SnackBar(ft.Text("Transferência Pix enviada com sucesso!"), bgcolor="green700")
                        else:
                            page.snack_bar = ft.SnackBar(ft.Text("Gateway recusou a transação. Verifique os dados."), bgcolor="red700")
                    except Exception:
                        page.snack_bar = ft.SnackBar(ft.Text("Falha na comunicação com o servidor bancário."), bgcolor="red700")

                state["saldo"] -= v
                state["pontos"] = int(state["saldo"] / 0.001)
                await salvar_progresso_local()
                await mostrar_tela_principal()
                
            page.snack_bar.open = True
            await page.update_async()

        palco.controls.extend([
            ft.Text("Solicitar Resgate Pix 💰", size=24, weight="bold"),
            ft.Container(content=ft.Column([
                ft.Text("📜 REGULAMENTO DE RETIRADA:", weight="bold", size=13, color="amber400"),
                ft.Text("• Limite de Saque Mínimo: R$ 10,00 por transação.", size=12),
                ft.Text("• Taxa Bancária: R$ 0,00 (Isento de tarifas).", size=12),
                ft.Text("• Processamento: Liquidado instantaneamente via API Gateway.", size=12),
            ], spacing=5), padding=12, bgcolor="#1a1a1a", border_radius=8, width=340),
            ft.Container(height=5),
            tipo_chave, campo_chave, campo_valor,
            ft.ElevatedButton("Confirmar Transação Pix 🚀", bgcolor="teal700", color="white", width=320, height=45, on_click=executar_saque_real),
            ft.TextButton("Voltar ao Menu Principal", on_click=mostrar_tela_principal)
        ])
        await page.update_async()

    # Dispara o carregamento do histórico local logo após desenhar a interface inicial
    page.run_task(carregar_sessao_salva)

if __name__ == "__main__":
    porta = int(os.getenv("PORT", 8080))
    ft.app(target=main, port=porta, assets_dir="assets")