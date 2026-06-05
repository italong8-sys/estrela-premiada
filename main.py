import flet as ft
import asyncio
import os
import requests  

async def main(page: ft.Page):
    page.title = "StarRun Premium"
    page.theme_mode = "dark"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.padding = 10
    
    # Palco central adaptável (Se adapta ao tamanho de PCs e Celulares automaticamente)
    palco = ft.Column(alignment="center", horizontal_alignment="center", max_width=480)
    page.controls.append(palco)
    await page.update_async() 
    
    # ==========================================
    # SISTEMA DE ÁUDIO ASSÍNCRONO BLINDADO
    # ==========================================
    snd_bg = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/ambient_space_drive.ogg", autoplay=False, volume=0.25, release_mode="loop")
    snd_jump = ft.Audio(src="https://actions.google.com/sounds/v1/cartoon/slide_whistle_up.ogg", autoplay=False, volume=0.5)
    snd_point = ft.Audio(src="https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg", autoplay=False, volume=0.4)
    snd_over = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/space_emergency.ogg", autoplay=False, volume=0.6)
    
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
        "star_bottom": 0.0, 
        "obstacle_left": 340, 
        "obstacle_speed": 7.0,
        "score_session": 0, 
        "fase_atual": 1,
        "tela_cheia": False  # Controle dinâmico de redimensionamento
    }

    cores_cenarios = {"Espaço Oblívio": "#111111", "Deserto Escaldante": "#3a2212", "Cyberpunk Neon": "#1a0033"}

    # --- CARREGAMENTO DO STORAGE TOTALMENTE ASSÍNCRONO ---
    async def carregar_sessao_salva():
        try:
            await asyncio.sleep(0.3) # Delay de segurança para estabilizar o canal WebSocket
            s = await page.client_storage.get_async("starrun_saldo")
            if s is not None: state["saldo"] = float(s)
            
            p = await page.client_storage.get_async("starrun_pontos")
            if p is not None: state["pontos"] = int(p)
            
            a = await page.client_storage.get_async("starrun_ads")
            if a is not None: state["anuncios_assistidos"] = int(a)
            
            sk = await page.client_storage.get_async("starrun_skin")
            if sk is not None: state["skin_atual"] = sk
            
            ce = await page.client_storage.get_async("starrun_cenario")
            if ce is not None: state["cenario_atual"] = ce
            
            skins_salvas = await page.client_storage.get_async("starrun_inv_skins")
            if skins_salvas: state["skins_desbloqueadas"] = skins_salvas.split(",")
            
            cenarios_salvos = await page.client_storage.get_async("starrun_inv_cenarios")
            if cenarios_salvos: state["cenarios_comprados"] = cenarios_salvos.split(",")
        except Exception as err:
            print(f"Erro Storage Load: {err}")

    async def salvar_progresso_local():
        try:
            await page.client_storage.set_async("starrun_saldo", str(state["saldo"]))
            await page.client_storage.set_async("starrun_pontos", str(state["pontos"]))
            await page.client_storage.set_async("starrun_ads", str(state["anuncios_assistidos"]))
            await page.client_storage.set_async("starrun_skin", state["skin_atual"])
            await page.client_storage.set_async("starrun_cenario", state["cenario_atual"])
            await page.client_storage.set_async("starrun_inv_skins", ",".join(state["skins_desbloqueadas"]))
            await page.client_storage.set_async("starrun_inv_cenarios", ",".join(state["cenarios_comprados"]))
        except Exception as err:
            print(f"Erro Storage Save: {err}")

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
            await snd_bg.play_async() # Inicia som ambiente com segurança assíncrona
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
                    padding=15, width=340
                )
            ),
            ft.Text(f"Vidas: {state['vidas']} ❤️ | Skin: {state['skin_atual']} | Mapa: {state['cenario_atual']}", size=12, color="white54", text_align="center"),
            ft.Container(height=15),
            ft.ElevatedButton("Jogar Corrida Estelar 🕹️", bgcolor="green700", color="white", width=280, height=45, on_click=mostrar_tela_jogo),
            ft.ElevatedButton("Loja de Cenários 🛒", bgcolor="blue700", color="white", width=280, height=45, on_click=mostrar_loja_cenarios),
            ft.ElevatedButton("Desbloquear Skins 📺", bgcolor="purple700", color="white", width=280, height=45, on_click=mostrar_loja_skins),
            ft.ElevatedButton("Sacar via Pix 💰", bgcolor="teal700", color="white", width=280, height=45, on_click=mostrar_tela_pix),
        ])
        await page.update_async()

    # ==========================================
    # TELA 2: MOTOR GRÁFICO DO JOGO (PC & CELULAR)
    # ==========================================
    async def mostrar_tela_jogo(e=None):
        palco.controls.clear()
        state["star_bottom"] = 0
        state["score_session"] = 0
        state["fase_atual"] = 1

        # Calcula a largura com base no ajuste de tela selecionado
        largura_arena = min(page.width - 20, 550) if state["tela_cheia"] else 350
        altura_arena = 200 if state["tela_cheia"] else 140
        state["obstacle_left"] = largura_arena - 20

        star = ft.Container(content=ft.Text(state["skin_atual"], size=26), left=40, bottom=0)
        obstacle = ft.Container(content=ft.Text("🌵", size=24), left=state["obstacle_left"], bottom=0)
        chao = ft.Container(width=largura_arena, height=2, bgcolor="white54", bottom=0)
        
        game_stack = ft.Stack([chao, star, obstacle], width=largura_arena, height=altura_arena)
        
        async def realizar_pulo(event_data):
            if not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 15.0
                await snd_jump.play_async()  

        conteudo_jogo = ft.Container(
            content=game_stack, width=largura_arena, height=altura_arena,
            bgcolor=cores_cenarios.get(state["cenario_atual"], "#111111"),
            border_radius=10, border=ft.Border.all(width=1, color="white24"),
            on_click=realizar_pulo
        )

        async def d_teclado(k: ft.KeyboardEvent):
            if k.key in ["Space", "Arrow Up"] and not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 15.0
                await snd_jump.play_async()

        page.on_keyboard_event = d_teclado

        placar_vidas = ft.Text(f"Vidas: {state['vidas']} ❤️", size=15, weight="bold", color="green400")
        placar_pontos = ft.Text("Pontos: 0", size=15, weight="bold")
        placar_fase = ft.Text("Fase: 1", size=15, weight="bold", color="amber400")
        text_instrucao = ft.Text("Toque no cenário para pular!", size=13, color="white40", text_align="center")

        async def game_loop():
            gravity = 1.50
            while state["running"]:
                # Arena dinâmica lê o tamanho em tempo real para wrap-around fluído
                limite_arena = min(page.width - 20, 550) if state["tela_cheia"] else 350
                
                state["obstacle_left"] -= state["obstacle_speed"]
                if state["obstacle_left"] < -15:
                    state["obstacle_left"] = limite_arena - 20
                    state["score_session"] += 10
                    placar_pontos.value = f"Pontos: {state['score_session']}"
                    await snd_point.play_async()  
                    
                    nova_fase = (state["score_session"] // 100) + 1
                    if nova_fase != state["fase_atual"]:
                        state["fase_atual"] = nova_fase
                        placar_fase.value = f"Fase: {state['fase_atual']}"
                        state["obstacle_speed"] += 1.5
                        if state["fase_atual"] == 2 and "🚀" not in state["skins_desbloqueadas"]:
                            state["skins_desbloqueadas"].append("🚀")
                            await salvar_progresso_local()
                
                if state["is_jumping"]:
                    state["star_bottom"] += state["velocity_y"]
                    state["velocity_y"] -= gravity
                    if state["star_bottom"] <= 0:
                        state["star_bottom"] = 0
                        state["is_jumping"] = False
                
                star.bottom = state["star_bottom"]
                obstacle.left = state["obstacle_left"]
                
                # Colisão matemática adaptada para altura expandida
                if (25 <= state["obstacle_left"] <= 55) and state["star_bottom"] <= 20:
                    state["running"] = False
                    await snd_over.play_async()  
                    break
                
                await conteudo_jogo.update_async()
                await placar_pontos.update_async()
                await asyncio.sleep(0.04)

            state["vidas"] -= 1
            await atualizar_financeiro(state["score_session"])
            botao_iniciar.text = "Jogar Novamente 🔄"
            botao_iniciar.visible = True
            
            if state["vidas"] <= 0:
                botao_iniciar.visible = False
                container_anuncio.visible = True
                text_instrucao.value = "Energia esgotada! Assista ao anúncio para recarregar."
                text_instrucao.color = "amber400"
            else:
                text_instrucao.value = f"Fim de jogo! Restam {state['vidas']} energias."
                text_instrucao.color = "red400"
                
            placar_vidas.value = f"Vidas: {state['vidas']} ❤️"
            await page.update_async()

        async def disparar_inicio(e):
            if state["vidas"] <= 0: return
            state["running"] = True
            state["obstacle_speed"] = 7.0
            botao_iniciar.visible = False
            await page.update_async()
            asyncio.create_task(game_loop())

        async def recarregar_vidas_anuncio(e):
            await page.launch_url_async("https://omg10.com/4/11105173")
            state["vidas"] = 3
            container_anuncio.visible = False
            botao_iniciar.visible = True
            placar_vidas.value = f"Vidas: {state['vidas']} ❤️"
            state["anuncios_assistidos"] += 1
            await salvar_progresso_local()
            await mostrar_tela_jogo()

        async def alternar_redimensionamento(e):
            state["tela_cheia"] = not state["tela_cheia"]
            await mostrar_tela_jogo()

        botao_iniciar = ft.ElevatedButton("Iniciar Corrida 🚀", bgcolor="green700", color="white", width=200, on_click=disparar_inicio)
        container_anuncio = ft.Column([
            ft.ElevatedButton("Assistir Vídeo Premiado 📺", icon="play_circle", bgcolor="amber700", color="black", on_click=recarregar_vidas_anuncio)
        ], alignment="center")

        container_anuncio.visible = True if state["vidas"] <= 0 else False
        if state["vidas"] <= 0: botao_iniciar.visible = False

        btn_modo_tela = ft.IconButton(
            icon=ft.icons.FULLSCREEN_EXIT if state["tela_cheia"] else ft.icons.FULLSCREEN,
            icon_color="amber400",
            tooltip="Alternar ajuste de tela",
            on_click=alternar_redimensionamento
        )

        palco.controls.extend([
            ft.Row([ft.Text("🕹️ Arena StarRun", size=18, weight="bold"), btn_modo_tela], alignment="space_between", width=largura_arena),
            ft.Row([placar_vidas, placar_fase, placar_pontos], alignment="space_around", width=largura_arena),
            ft.Container(height=5),
            conteudo_jogo,
            ft.Container(height=15, content=text_instrucao),
            ft.Row([botao_iniciar, container_anuncio], alignment="center"),
            ft.Container(height=10),
            ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)
        ])
        await page.update_async()

    # ==========================================
    # TELA 3: LOJA DE CENÁRIOS
    # ==========================================
    async def mostrar_loja_cenarios(e=None):
        palco.controls.clear()
        lista_loja = ft.Column(spacing=12, horizontal_alignment="center")
        ofertas = [
            {"nome": "Espaço Oblívio", "preco": 0, "desc": "Cenário original do jogo."},
            {"nome": "Deserto Escaldante", "preco": 500, "desc": "Fundo arenoso clássico."},
            {"nome": "Cyberpunk Neon", "preco": 1500, "desc": "Neon futurista de alta performance."}
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

            lista_loja.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(item["nome"], weight="bold", size=15), ft.Text(item["desc"], size=11, color="white54")], expand=True), btn]), padding=10, border=ft.Border.all(1, "white24"), border_radius=8, width=350))

        palco.controls.extend([ft.Text("Loja de Cenários 🛒", size=24, weight="bold"), ft.Text(f"Seu Saldo: {state['pontos']} Pontos", color="amber400"), ft.Container(height=5), lista_loja, ft.Container(height=15), ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)])
        await page.update_async()

    # ==========================================
    # TELA 4: LOJA DE SKINS
    # ==========================================
    async def mostrar_loja_skins(e=None):
        palco.controls.clear()
        lista_skins = ft.Column(spacing=12, horizontal_alignment="center")
        catalogo = [
            {"skin": "⭐", "tipo": "Livre", "req": 0, "info": "A estrela clássica padrão."},
            {"skin": "☄️", "tipo": "Anúncios", "req": 2, "info": "Meteoro de Fogo (2 Ads)."},
            {"skin": "🛸", "tipo": "Anúncios", "req": 5, "info": "Disco Alienígena (5 Ads)."},
            {"skin": "🚀", "tipo": "Fase", "req": 2, "info": "Liberado na Fase 2 automaticamente."}
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
            elif item["tipo"] == "Fase": btn = ft.Text(f"Fase {item['req']}", color="red400", size=12, weight="bold")
            else: btn = ft.ElevatedButton(f"Ver Vídeo ({state['anuncios_assistidos']}/{item['req']})", bgcolor="purple700", color="white", width=120, on_click=assistir_ad_skin)

            lista_skins.controls.append(ft.Container(content=ft.Row([ft.Text(item["skin"], size=28), ft.Column([ft.Text(item["info"], size=11, color="white70")], expand=True), btn]), padding=10, border=ft.Border.all(1, "white12"), border_radius=8, width=350))

        palco.controls.extend([ft.Text("Skins Desbloqueáveis 📺", size=24, weight="bold"), ft.Text(f"Histórico: {state['anuncios_assistidos']} anúncios assistidos", color="purple300"), ft.Container(height=5), lista_skins, ft.Container(height=15), ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)])
        await page.update_async()

    # ==========================================
    # TELA 5: PAINEL PIX REAL ONLINE
    # ==========================================
    async def mostrar_tela_pix(e=None):
        palco.controls.clear()
        tipo_chave = ft.Dropdown(label="Tipo de Chave", width=320, options=[ft.dropdown.Option("CPF"), ft.dropdown.Option("E-mail"), ft.dropdown.Option("Telefone")])
        campo_chave = ft.TextField(label="Insira sua Chave Pix", width=320)
        campo_valor = ft.TextField(label="Valor do Resgate (R$)", width=320, value=f"{state['saldo']:.2f}")

        async def ejecutar_saque_real(e):
            try:
                v = float(campo_valor.value.replace(",", "."))
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor="red700")
                page.snack_bar.open = True
                await page.update_async()
                return

            if not tipo_chave.value or not campo_chave.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os dados Pix!"), bgcolor="red700")
            elif v > state["saldo"]:
                page.snack_bar = ft.SnackBar(ft.Text("Saldo insuficiente!"), bgcolor="red700")
            elif v < 10.00:
                page.snack_bar = ft.SnackBar(ft.Text("Saque mínimo obrigatório: R$ 10,00!"), bgcolor="amber800")
            else:
                API_TOKEN = os.getenv("GATEWAY_PIX_TOKEN", "DESATIVADO")
                
                if API_TOKEN == "DESATIVADO":
                    page.snack_bar = ft.SnackBar(ft.Text("Modo Sandbox: Chave válida, mas API externa pendente no Render!"), bgcolor="amber900")
                else:
                    payload = {"key": campo_chave.value, "type": tipo_chave.value, "amount": v}
                    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
                    
                    try:
                        response = requests.post("https://api.asaas.com/v3/transfers", json=payload, headers=headers, timeout=10)
                        if response.status_code in [200, 201]:
                            page.snack_bar = ft.SnackBar(ft.Text("Pix realizado com sucesso!"), bgcolor="green700")
                        else:
                            page.snack_bar = ft.SnackBar(ft.Text("Gateway recusou o Pix."), bgcolor="red700")
                    except Exception:
                        page.snack_bar = ft.SnackBar(ft.Text("Erro de conexão com o banco externo."), bgcolor="red700")

                state["saldo"] -= v
                state["pontos"] = int(state["saldo"] / 0.001)
                await salvar_progresso_local()
                await mostrar_tela_principal()
                
            page.snack_bar.open = True
            await page.update_async()

        palco.controls.extend([
            ft.Text("Solicitar Resgate Pix 💰", size=24, weight="bold"),
            ft.Container(content=ft.Column([
                ft.Text("📜 TERMOS DE RETIRADA:", weight="bold", size=13, color="amber400"),
                ft.Text("• Saque Mínimo Obrigatório: R$ 10,00.", size=12),
                ft.Text("• Taxa de Conveniência: R$ 0,00 (Isento).", size=12),
                ft.Text("• Janela de Transação: Processamento instantâneo via API Gateway.", size=12),
            ], spacing=5), padding=12, bgcolor="#1a1a1a", border_radius=8, width=340),
            ft.Container(height=10),
            tipo_chave, campo_chave, campo_valor,
            ft.ElevatedButton("Confirmar Transação Pix 🚀", bgcolor="teal700", color="white", width=320, height=45, on_click=ejecutar_saque_real),
            ft.TextButton("Voltar ao Menu Principal", on_click=mostrar_tela_principal)
        ])
        await page.update_async()

    # Fluxo de carregamento inicial seguro
    await carregar_sessao_salva()
    await mostrar_tela_principal()

if __name__ == "__main__":
    porta = int(os.getenv("PORT", 8080))
    ft.app(target=main, port=porta, assets_dir="assets")